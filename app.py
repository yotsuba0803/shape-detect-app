import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# --- Streamlit 設定 ---
st.set_page_config(page_title="Fe–H2O Pourbaix Diagram", layout="wide")
st.markdown("""
<div style="background: linear-gradient(135deg,#0f172a,#1e3a8a);
            color:white; padding:1.5rem; border-radius:12px; text-align:center;">
    <h1>Fe–H2O Pourbaix Diagram (Oxides / Hydroxides selectable)</h1>
</div>
""", unsafe_allow_html=True)

# --- サイドバー ---
with st.sidebar:
    st.header("Parameters")
    temp_c = st.slider("Temperature [°C]", 0, 100, 25)
    log_a_fe2 = st.number_input("log10(Fe2+ activity)", value=-6.0, format="%.1f")
    log_a_fe3 = st.number_input("log10(Fe3+ activity)", value=-6.0, format="%.1f")
    phase_type = st.radio("Select phase type", ["Oxides only", "Hydroxides only"])
    show_boundary = st.checkbox("Show boundary lines", value=True)

    # (5) 表示切替：沈殿領域だけ強調表示
    highlight_precip_only = st.checkbox("Highlight precipitation only", value=True)

# --- 定数 ---
F = 96485.3
R = 8.31446
T = 273.15 + temp_c
S = R*T*np.log(10)/F
act_fe2 = log_a_fe2 * S
act_fe3 = log_a_fe3 * S
G_H2O = -237130  # J/mol

# --- 標準生成ギブズ [J/mol] ---
Gf = {
    "Fe": 0.0,
    "Fe2+": -78900,
    "Fe3+": -4700,
    "Fe(OH)2": -486500,
    "Fe(OH)3": -696500,
    "Fe3O4": -1015400,
    "Fe2O3": -742200,
    "HFeO2-": -379000
}

# --- Meshgrid ---
res = 600
ph_vec = np.linspace(0, 14, res)
e_vec = np.linspace(-2.5, 2.5, res)
PH, E = np.meshgrid(ph_vec, e_vec)

# --- Psi 計算関数 ---
def calc_psi(PH, E, phase_type):
    Psi = {}
    Psi["Fe"] = np.full_like(PH, Gf["Fe"]/F)
    Psi["Fe2+"] = Gf["Fe2+"]/F + act_fe2 - 2*E
    Psi["Fe3+"] = Gf["Fe3+"]/F + act_fe3 - 3*E
    Psi["HFeO2-"] = (Gf["HFeO2-"] - 2*G_H2O)/F - 2*E - 3*S*PH + act_fe2

    if phase_type == "Hydroxides only":
        Psi["Fe(OH)2"] = (Gf["Fe(OH)2"] - 2*G_H2O)/F - 2*E - 2*S*PH + act_fe2
        Psi["Fe(OH)3"] = (Gf["Fe(OH)3"] - 3*G_H2O)/F - 3*E - 3*S*PH + act_fe3
    else:  # Oxides only
        Psi["Fe3O4"] = ((Gf["Fe3O4"] - 4*G_H2O)/F - 8*E - 8*S*PH)/3
        Psi["Fe2O3"] = ((Gf["Fe2O3"] - 3*G_H2O)/F - 6*E - 6*S*PH)/2

    return Psi

Psi_dict = calc_psi(PH, E, phase_type)

# --- 使用フェーズキー選択 ---
if phase_type == "Hydroxides only":
    psi_keys = ["Fe", "Fe2+", "Fe3+", "Fe(OH)2", "Fe(OH)3", "HFeO2-"]
    precip_phases = ["Fe(OH)2", "Fe(OH)3"]
else:
    psi_keys = ["Fe", "Fe2+", "Fe3+", "Fe3O4", "Fe2O3", "HFeO2-"]
    precip_phases = ["Fe3O4", "Fe2O3"]

Psi_stack = np.stack([Psi_dict[k] for k in psi_keys], axis=0)
phase_map = np.argmin(Psi_stack, axis=0)

# --- 沈殿領域マスク作成（固相が最安定の領域） ---
precip_indices = [psi_keys.index(p) for p in precip_phases if p in psi_keys]
precip_mask = np.isin(phase_map, precip_indices)

# --- 描画 ---
fig, ax = plt.subplots(figsize=(10, 8), dpi=120)

if highlight_precip_only:
    # 0: 非沈殿（グレー）, 1: 沈殿（色）
    # ※色はここで1色だけに統一（例：赤）
    show_map = precip_mask.astype(int)
    cmap2 = ListedColormap(["#9ca3af", "#ef4444"])  # 灰 + 赤
    ax.imshow(
        show_map,
        origin='lower',
        cmap=cmap2,
        extent=[0, 14, -2.5, 2.5],
        aspect='auto'
    )
else:
    # 従来どおり相をカラフル表示（参考として残す）
    colors = ['#94a3b8','#3b82f6','#facc15','#60a5fa','#f87171','#a855f7','#22c55e','#fb923c']
    ax.imshow(
        phase_map,
        origin='lower',
        cmap=ListedColormap(colors[:len(psi_keys)]),
        extent=[0, 14, -2.5, 2.5],
        aspect='auto'
    )
    # 半透明で沈殿を重ねる
    ax.contourf(PH, E, precip_mask.astype(int), levels=[0.5, 1.5], colors=["black"], alpha=0.18)

# 水の分解線
ax.plot(ph_vec, 1.229 - S*ph_vec, 'k--', alpha=0.4)
ax.plot(ph_vec, 0.0 - S*ph_vec, 'k--', alpha=0.4)

# 境界線（相境界なので、沈殿だけ強調モードでも引ける）
if show_boundary:
    line_style = {'colors': 'white', 'linewidths': 0.7, 'alpha': 0.6}
    psi_list = [Psi_dict[k] for k in psi_keys]
    for i in range(len(psi_list)):
        for j in range(i+1, len(psi_list)):
            ax.contour(PH, E, psi_list[i] - psi_list[j], levels=[0], **line_style)

# 沈殿相ラベル（沈殿だけ強調表示のときに限定して表示）
if highlight_precip_only:
    for p in precip_phases:
        if p in psi_keys:
            idx = psi_keys.index(p)
            mask = (phase_map == idx)
            if np.any(mask):
                ph_c = PH[mask].mean()
                e_c = E[mask].mean()
                ax.text(
                    ph_c, e_c, p, color='black', fontsize=10, ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round')
                )

ax.set_xlabel("pH")
ax.set_ylabel("Potential E [V vs SHE]")
ax.set_xlim(0, 14)
ax.set_ylim(-2.5, 2.5)
ax.grid(alpha=0.1)
ax.set_title(
    f"Fe–H2O Pourbaix Diagram @ {temp_c}°C, log a(Fe2+)={log_a_fe2}, log a(Fe3+)={log_a_fe3}"
)

# 凡例（沈殿／非沈殿）
if highlight_precip_only:
    leg = [
        Patch(facecolor="#ef4444", edgecolor="none", label="Precipitation (solid stable)"),
        Patch(facecolor="#9ca3af", edgecolor="none", label="No precipitation (aqueous/metal stable)")
    ]
    ax.legend(handles=leg, loc="upper right", framealpha=0.95)

st.pyplot(fig)



