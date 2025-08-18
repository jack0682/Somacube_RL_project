# RL Training Roadmap v3.1 — **정합-유도 보상 & 신뢰도 게이팅 기반 SAC 학습 플랜 (지금 당장 시작용)**

*(Doosan M0609 + 2F Gripper + RealSense D435i + ROS 2 Humble + YOLOv8n, repo at `~/ros2_ws/src/`)*

> “지금부터의 모든 학습은 **정합 품질 벡터**를 보상의 핵으로, **정합 신뢰도**를 행동 게이팅의 축으로 삼는다.”
> 아래 계획은 이미 구축된 **Day-0(오늘) 파이프라인**을 전제로, **내일 아침부터 곧장 학습**을 굴릴 수 있는 **세부 절차·하이퍼파라미터·스케줄·안전 램프업**을 포함한다. 실행 명령은 ROS 2 기준으로 제공하며, 코드는 반드시 `~/ros2_ws/src/` 구조를 직접 확인한 뒤(`tree ~/ros2_ws/src` 등) 적용한다.

---

## 1) 학습 목표·운영 제약(200+ words)

**핵심 목표**는 ① 1층(평면) 정렬·착좌의 **피크 힘 25%↓** 또는 **정렬 시간 15%↓**(PD 대비) 중 최소 1개 달성과, ② **재시도 횟수 30%↓**다. RL은 **저수준 미세 접촉 제어(Δx,Δy,Δyaw)** 만 담당하고, **고수준 시퀀싱/리그라스프/대안 접근**은 기존 시퀀서가 계속 관리한다. 이 **역할 분리**는 학습 실패가 전체 파이프라인을 깨뜨리지 않도록 한다. 또한, 실기를 다루므로 **행동 투영(게이팅)** 과 **임피던스 제어**는 항상 켜져 있어야 하며, RL 출력은 이 **안전 래퍼**를 반드시 통과한다.

**운영 제약**은 세 가지다. 첫째, **센서→정합→품질**의 지연 상한(평균 60 ms, p95 90 ms)을 넘지 않도록 학습 루프에서 **관측/행동 레이트**를 20–50 Hz로 제한한다. 둘째, **데이터 효율**을 위해 초기에는 **Behavior Cloning(BC)** 으로 예열하고, 이어 **SAC 오프폴리시**로 미세 조정한다. 셋째, **랩-세이프티**: 힘/토크/속도 위반 시 **Back-off→재관측→재정합**을 자동 트리거하며, 연속 위반은 즉시 **Clamp 단계**로 롤백한다. 마지막으로, **로그·KPI**는 ROS 토픽 + CSV에 동시 기록되어야 하며, 학습 중단/재개가 가능하도록 **체크포인트** 주기를 5–10 분으로 설정한다.

---

## 2) 데이터·예열(BC) 계획 — **내일 오전 2시간 내 끝내는 프리트레인**(200+ words)

**데이터 소스**는 Day-0에서 수집한 **PD 기반 10–15 에피소드**와, 아침 추가로 10 에피소드(총 20–25)에 해당한다. 각 에피소드는 `/pc_register/pose`, `/pc_register/quality`, `/pose/filtered`, `/ee/ft`, `/policy/lo/cmd`, `/safety/events` 를 공통 시간축으로 가진다(rosbag + 텐서 로그). **관측 텐서**는

$$
s_t=\big[\Delta x,\Delta y,\Delta z,\Delta\psi,\ \overline{d}_{\perp},\ d_{\text{Chamfer}},\ \rho_{\text{in}},\ \sigma_{\text{ICP}},\ F_z,\ \|\dot{\mathbf{F}}\|,\ \text{grip},\ \text{gains}\big]
$$

로 구성하며, **행동 라벨** $a_t$는 PD가 냈던 $(\Delta x,\Delta y,\Delta\psi)$ (및 선택적으로 $\Delta z,\ \Delta K_p,\ \Delta D$)를 사용한다. **정합 품질 항**은 반드시 **z-score 정규화**하고, 힘/충격 계열은 **단위 일치**를 위해 N, N/s 기준으로 **0-mean, unit-var** 스케일러를 학습 세트 통계로 고정한다(실기 드리프트를 막기 위해 업데이트는 온라인 중지).

**BC 손실**은 MSE + 미세한 행동 라벨 클리핑($|\Delta x|,|\Delta y|\le 3\mathrm{mm},\ |\Delta\psi|\le 1.5^\circ$)로 하고, **행동 라벨 신뢰도 가중**을 도입한다. 가중 $w_t=\operatorname{sigmoid}(a\cdot\rho_{\text{in}}-b)$ 로 정의하여 **inlier가 낮은 구간의 라벨 영향**을 약화한다(예: $a=10,b=5$). 옵티마이저는 AdamW(lr $3\cdot10^{-4}$, weight\_decay $10^{-4}$), 15–30 분 내 수렴을 목표로 한다. **조기 종료** 기준은 검증 MSE가 20 에폭 내 개선 없을 때, 또는 유효 행동률(클리핑 미적용 비율)이 85% 미만으로 떨어질 때다. 완성된 BC 정책은 **Clamp 0.3**(Δ상한 30%)에서 바로 검증한다(10 에피소드). 이 단계가 성공하면 SAC 온라인 파인튜닝으로 넘어간다.

---

## 3) 온라인 RL 설정 — **SAC(Soft Actor-Critic) with safety projection**(200+ words)

**행동 공간**은 $\mathbf{a}=[\Delta x,\Delta y,\Delta z,\Delta\psi]$ 이고, 1층 학습에서는 $\Delta z$ 를 **접근/착좌 구간에서만** 허용한다(정렬은 planar). **게이팅 투영**은

$$
\|\Delta\mathbf{x}_{xy}\|\le\delta_{\max}(\hat\sigma),\quad |\Delta\psi|\le\theta_{\max}(\hat\sigma),
$$

를 강제하며, $\delta_{\max},\theta_{\max}$ 는 §6의 선형 보간식으로 실시간 산출한다. **SAC 하이퍼파라미터**는 다음을 기본으로 한다: $\gamma=0.995$, actor/critic lr $3\cdot10^{-4}$, 타깃 $\tau=0.005$, replay $10^6$, 배치 512, 엔트로피 **auto-tune**(target $H=-\text{dim}(\mathbf{a})\approx -4$). **Q-네트워크 2개**(twin critics), **policy delay=2**, **grad clip=10.0**, **layer: 256-256-128**(ReLU), **log-std clamp** $[-5,2]$.

업데이트는 환경 1 step당 **최대 1–2회**(real-time 제약), **target 업데이트**는 매 스텝 Polyak. **우선순위 리플레이**는 선택(안정성 유지 위해 초반 OFF 권장). **관측 정규화**는 **RunningMeanStd**(초기 Day-0 통계로 freeze)로 하고, 정합 항의 스케일이 급변할 수 있는 **Alt-View/재정합 시점**에는 **마스크**를 걸어 보상 장기 분산을 억제한다. **학습 단계 제약**: 성공률이 60% 미만인 동안은 **Clamp 0.5** 이상으로 올리지 않는다; 성공률이 이동평균 75%를 넘고, 위반률(힘/속도) <2%일 때만 **Clamp 0.7→1.0**으로 상승한다. 모든 행동은 임피던스 래퍼를 통해 전달되며, **Back-off**가 발생하면 현 스텝 보상에 **패널티**($-\delta\cdot\|\Delta\mathbf{x}\| - \zeta\cdot\|\dot{\mathbf{F}}\|$)가 부과된다.

---

## 4) 커리큘럼·클램프 램프업 — **L1→L2→L3**(200+ words)

**L1(정렬 완화)**: 공차 $3–5$ mm, yaw 허용 $3–4^\circ$. 보상은 **지오데식 각/점-평면** 항 비중을 높이고(예: $w_{geod}=1.2, w_{p2p}=0.8$), 충격/힘 패널티는 낮게 시작($w_F=0.6, w_{jerk}=0.2$). **Clamp=0.3→0.5** 범위에서만 업데이트. **졸업 기준**: 200 에피 윈도 성공률 85% 이상, 평균 $d_R\le 2.0^\circ$.

**L2(정밀 정렬)**: 공차 $1–2$ mm, yaw $2^\circ$. 힘/충격 패널티를 상향($w_F=1.0, w_{jerk}=0.3$), inlier 비중 $w_{inlier}=0.2$ 유지. **Clamp=0.5→0.7**. **졸업 기준**: 성공률 80% 이상, $\overline{d}_{\perp}\le 1$ mm, Back-off 평균 ≤ 0.5/에피.

**L3(착좌-세들)**: 삽입 프로그레스 항 $w_{insert}=0.7$ 활성화, **가변 임피던스** 스케줄(진전↑ ⇒ $K_p\downarrow,D\uparrow$). **Clamp=0.7→1.0**. **졸업 기준**: 피크 $F_z$ **PD 대비 ≥ 25% 감소** 또는 정렬 시간 ≥ 15% 단축. **퇴행 방지**: L3에서 실패률↑ 시 즉시 L2로 롤백하고, 엔트로피 타깃을 일시적으로 완화(탐색↑).

모든 레벨은 **Alt-View/재정합 트리거**가 잦을수록(즉, $\rho_{\text{in}}$ 낮음) **Clamp 자동 하향**(§6)과 **샘플 가중**(inlier 기반)을 동시에 적용한다. 커리큘럼 레벨 전환은 시퀀서의 **완료 플래그**와 KPI가 함께 충족될 때만 이뤄진다. 이 설계는 **현실 세계의 가림·광원 변화**를 암묵적으로 포함하며, 레벨이 오를수록 **도메인 랜덤화 강도**(깊이 노이즈, 마찰계수)도 함께 조금씩 올린다(시뮬 보조 시).

---

## 5) 관측·행동·보상 스펙(숫자 고정안)(200+ words)

**관측** $s_t$:

*   기하 오차: $\Delta x,\Delta y,\Delta z,\Delta\psi$ (목표 대비), 정규화 범위 $\pm 10$ mm / $\pm 10^\circ$.
*   정합 품질: $\overline{d}_{\perp}$(m), $d_{\text{Chamfer}}$(m), $\rho_{\text{in}}$, $\sigma_{\text{ICP}}$(m), $d_R$(deg). z-score normalize(고정 통계).
*   힘/충격: $F_z$(N), $\|\dot{\mathbf{F}}\|$(N/s).
*   상태 컨텍스트: 그리퍼 개구량, 현재 임피던스 게인 스케일.

**행동** $\mathbf{a}_t$: $\Delta x,\Delta y,\Delta z,\Delta\psi$ (m, rad). **tanh** 사전출력 → **스케일** → **게이팅 투영** 순서. 1층에서는 주로 $\Delta x,\Delta y,\Delta\psi$ 를 사용, $\Delta z$ 는 pre-place/settle에서만 활성.

**보상** $R_t$ (값 제안):

$$
\begin{aligned}
R_t&=-1.2\,d_R^{(\deg)} - 0.8\,\overline{d}_{\perp}^{(\mathrm{mm})} - 0.5\,d_{\text{Chamfer}}^{(\mathrm{mm})}\
&\quad - 1.0\,\max(0,F_z-F_{\max}) - 0.3\,\|\dot{\mathbf{F}}\| + 0.7\,\Delta d_{\text{insert}} + 3.0\,\mathbf{1}_{\text{seat}}.
\end{aligned}
$$

여기서 거리 계열은 **mm 단위**로 환산하여 직관적 스케일을 맞춘다(코드에서 변환 일관성 주의). `seat`는 착좌 이벤트(평판 조건)로 1회 보너스. **끝보상**은 주지 않는다(스파스화 억제). **클리핑**: 개별 항 절대값 5.0 상한, 총 보상 $[-10, +5]$ 범위로 제한. **부호 검증**: 모든 오차/위반 항은 음수 기여, 진전/착좌는 양수. **로그**에서는 각 항의 기여를 CSV 컬럼으로 분리하여 **스케일 쏠림**을 상시 감시한다(한 항이 > 90% 지배 금지).

---

## 6) 안전 게이팅·임피던스 스케줄(수식·수치)(200+ words)

**정규화된 신뢰도:**

$$
\hat\sigma=\operatorname{clip}\frac{\sigma_{\text{ICP}}-0}{0.010-0},\;\; \hat\rho=\operatorname{clip}\frac{\rho_{\text{in}}-0.2}{0.8-0.2}.
$$

**각·평면 상한:**

$$
\theta_{\max}(\hat\sigma)=2.0^\circ\cdot (1-0.75\hat\sigma),\qquad
\delta_{\max}(\hat\rho)=4\,\mathrm{mm}\cdot (0.3+0.7\hat\rho).
$$

즉, $\sigma_{\text{ICP}}$ 커질수록 각도 스텝은 **최대 0.5°** 수준까지, $\rho_{\text{in}}$ 작을수록 평면 스텝은 **최소 1.2 mm** 수준까지 줄어든다. 속도/가속 상한도 같은 스케일로 축소(예: 0.4–1.0×). **힘 한계**는 바닥층에서 $F_{\max}=18$ N, $\|\dot{\mathbf{F}}\|$ 임계는 60–80 N/s 범위로 시작. **Back-off 매크로**: 위반 시 $(-\Delta x,-\Delta y,-2\mathrm{mm})$ 로 0.5× 속도로 이동 → 0.2 s 정지 → 재스캔/재정합 → 동일 실패 3회면 **Alt-View** → 그래도 실패면 **셀 스킵**.

**임피던스 스케줄**(착좌 진행 $\xi\in[0,1]$):

$$
K_p^{xy}(\xi)=K_{p0}^{xy}\big(1-0.4\,\xi\big),\quad D^{xy}(\xi)=D_{0}^{xy}\big(1+0.5\,\xi\big),
$$

기본값 $K_{p0}^{xy}=[800,800]\ \mathrm{N/m}$, $D_{0}^{xy}=[70,70]\ \mathrm{N\,s/m}$. 착좌 후 0.5 s 유지 시 그립 개방. 모든 스케일은 YAML에서 조정 가능하게 하고, **게이팅→임피던스→속도 포화** 순으로 적용(역순 금지). **안전 이벤트**는 `SafetyEvent` 로 즉시 퍼블리시하여 시퀀서가 **분기 로직**(재시도/Alt-View/스킵)을 일관되게 처리한다.

---

## 7) 인프라·체크포인트·KPI·평가(200+ words)

**체크포인트**: `~/.ros/somacube_ckpt/` 에 actor/critic/opt 상태를 **5–10 분 주기**로 저장(압축). **복구** 시에는 **관측 정규화 통계**와 **리플레이 버퍼 스냅샷**(선택)을 함께 복구, 불일치 시 자동 무시하고 냉시작. **KPI 토픽 `/kpi/state`** 에는 2 s 주기로 (성공률 이동평균, 평균 $d_R$, 평균 $\overline{d}_{\perp}$, 피크 $F_z$, 충격 적분, 재시도 평균, Alt-View 호출률, 재계산 시간)를 퍼블리시. **CSV 로그**는 `~/.ros/somacube_logs/DATE/`에 에피소드별 한 줄(요약) + 스텝별 테이블(세부) 두 종으로 저장.

**평가 프로토콜**은 (A) **PD-베이스라인**, (B) **BC-Only**, (C) **SAC(Clamp)**, (D) **SAC(Full)** 네 조건을 동일 시나리오 30 에피소드로 반복 후, **부트스트랩 95% CI** 를 산출한다. **주 지표**는 (i) 성공률, (ii) $\max F_z$, (iii) 정렬 시간, (iv) 재시도, (v) **갭/평탄도**(감사 스캔). **전이성 검사**로 조명, 깊이 노이즈, 마찰 변경(가능 시)을 **블록 무작위 6 세트**에 적용하고, **성능 유지율**을 보고한다. 모든 실험은 **시드 고정(≥3)** 으로 평균/분산을 함께 기록한다. **에러 카탈로그**(탭핑, 미스얼라인, 시야 가림, 과도한 Back-off)를 라벨링하여 **어블레이션**(게이팅 OFF, inlier 가중 OFF, jerk 패널티 OFF)으로 기여도를 분리한다.

---

## 8) 시간표·실행 명령 — **내일 아침 3-Step 램프**(200+ words)

**Step-A (09:30–10:30) — BC 프리트레인+검증**

*   `ros2 launch doosan_somacube_rl bringup_real.launch.py params:=config/rl_somacube_params.yaml`
*   `policy_sac_low` 를 **BC 모드**로 실행(`training.mode=BC`, `inference=clamp0.3`) → 30–45 분 학습.
*   검증 10 에피소드: 성공률≥70%, $d_R$·$\overline{d}_{\perp}$ DoD 준수 확인.

**Step-B (10:30–12:00) — SAC Clamp 0.5 온라인 파인튜닝**

*   `training.mode=SAC`, `safety_gating.clamp_scales=0.5`, `updates_per_step=1–2`.
*   2000–4000 환경스텝 동안 KPI 모니터링, 10 분마다 ckpt.
*   졸업 기준: 성공률≥75%, 위반률<2% → Clamp 0.7 승급.

**Step-C (13:00–15:30) — SAC Clamp 0.7→1.0 & L2/L3 전환**

*   Clamp 0.7에서 1500–3000 스텝 안정 후, L2 졸업조건 만족 시 L3 전환(+임피던스 스케줄).
*   **Full(=1.0)** 은 **연속 3 에피소드 무위반 + 성공률≥80%** 일 때만 허용.
*   15:30 이후 30-에피소드 평가(A/B/C/D 조건) 실행, 리포트 스크립트로 CI 산출.

**명령 예시(요지):**

```bash
# build & source
cd ~/ros2_ws && colcon build --packages-select doosan_somacube_rl && source install/setup.bash
# bringup
ros2 launch doosan_somacube_rl bringup_real.launch.py params:=config/rl_somacube_params.yaml
# bag (shadow or online)
bash ~/ros2_ws/src/doosan_somacube_rl/scripts/bag_record.sh
# topic sanity
ros2 topic hz /pc_register/quality ; ros2 topic echo /kpi/state --once
```

항상 **먼저** `tree -L 2 ~/ros2_ws/src` 로 실제 파일 구조를 확인하고, 커스텀 패키지가 **중복**될 경우 `-v2` 접미사로 안전 복제 후 적용한다.

---

## 9) 위험·디버깅 가이드(증상→원인→처치)(200+ words)

**증상 A — 보상 폭주(절댓값 > 10)**: 스케일 불일치. → **단위 변환**(m↔mm), 정합 항 z-score 재계산, 항목별 클리핑 확인. 로그에서 항별 기여율을 확인하여 **한 항 90%↑** 시 가중치 절반으로 낮추고 30 에피소드 재검.
**증상 B — 성공률↑인데 힘 위반↑**: 탐색 과세. → 엔트로피 타깃 $H$ 를 −3.5→−4.0으로 낮추고, Clamp 한 단계 하향(0.7→0.5). 임피던스 $D$ 10–20% 상향.
**증상 C — ICP 발산/점프**: occlusion/노이즈. → `max_corr_dist` 8→10 mm, Alt-View 프리셋 활성, `pose_tracker` EMA $\alpha$ 0.3→0.2, 점프 임계 8°→5°.
**증상 D — 학습 정체(Q overestimation)**: TD 타깃 분산. → target smoothing(critic target에 0.9 EMA), updates\_per\_step 감소, lr 절반, PER OFF.
**증상 E — 행동 포화(게이팅에 항상 막힘)**: 신뢰도 산출 범위 오류. → $\sigma_{\max},\rho_{\min/\max}$ 범위 재설정(로그 히스토그램 보고 5–95 퍼센타일에 맞추기), 스케일 하한(s\_{\theta}^{min}, s\_{\delta}^{min}) 0.25→0.4로 상향.
**증상 F — 재현 불가**: 시드·버전·YAML 불일치. → `logger` 가 **런치 해시(파일 체크섬)**, **시드**, **Git 커밋**을 KPI와 함께 기록하도록 설정. 동일 조건 재실행 의무화.

모든 처치는 **한 번에 하나**만 적용하고, 20–30 에피소드 관찰 후 유지/롤백을 결정한다. 실패 에피소드는 **원인 라벨**(tap/misalignment/occlusion/backoff loop)을 수작업으로 10건 정도 달아두면, 다음 파라미터 스윕의 방향성이 빨라진다.

---

## 10) 체크리스트(최소 실행조건)·핵심 수치 요약(200+ words)

**최소 실행조건**

*   [ ] `~/ros2_ws/src/` 실구조 확인(중복 패키지 없음).
*   [ ] `bringup_real.launch.py` 원클릭 기동, `/pc_register/quality` 30–60 Hz, p95 ≤ 90 ms.
*   [ ] 게이팅 함수 단조성 테스트 통과(유닛테스트), Back-off 2회 내 수렴.
*   [ ] BC 예열 완료(검증 성공률 ≥ 70%).
*   [ ] SAC Clamp 0.5 시작, KPI 대시보드 활성.

**핵심 수치 요약**

*   SAC: $\gamma=0.995$, lr $3\cdot10^{-4}$, $\tau=0.005$, batch 512, replay $10^6$, $H=-4$.
*   스케일: $\theta_{\max}\in[0.5^\circ,2.0^\circ]$, $\delta_{\max}\in[1.2,4.0]$ mm.
*   보상: 각/평면/Chamfer 가중 1.2/0.8/0.5, 힘/jerk 1.0/0.3, 진전 0.7, 착좌 3.0.
*   안전: $F_{\max}=18$ N, jerk 임계 60–80 N/s, 속도/가속 포화는 임피던스 래퍼에서 강제.
*   커리큘럼: L1(Clamp 0.3–0.5)→L2(0.5–0.7)→L3(0.7–1.0), 졸업 기준은 성공률·정밀·안전 복합.

> **요약 슬로건**: *“정합값은 보상, 정합 신뢰도는 브레이크.”*
> 이 원리를 학습 루프(보상), 안전 래퍼(투영), 커리큘럼(Clamp) 세 층에 **동일 수식**으로 적용하면, **학습 속도**와 **현실 안정성**이 동시에 오른다. 내일 오전 **BC 1시간 + SAC 2–4시간**만으로도 **PD 대비 피크힘 25%↓** 목표에 근접한 곡선을 얻을 수 있다. 실패해도 시스템은 **시퀀서·임피던스·게이팅** 덕분에 **깨지지 않는다**—이게 우리가 즉시 학습을 시작할 수 있는 이유다.

---

### 실행 전 마지막 메모

*   **반드시** `tree ~/ros2_ws/src` 로 클론 구조를 직접 확인하고(DoosanBootcamp3rd, YOLO, RealSense, `doosan_somacube_rl`), 충돌 시 `-v2` 패키지명으로 **비파괴 병치** 후 진행.
*   학습 스위치는 **YAML로만** 제어(BC↔SAC, Clamp 스케일, 보상 가중, 안전 한계).
*   KPI 스냅샷을 **매 스텝**이 아닌 **2 s** 간격으로 퍼블리시해 ROS 이벤트 폭주를 방지.
