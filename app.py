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
    show_precip = st.checkbox("Show precipitation region", value=True)

# --- 定数 ---
F = 96485.3
R = 8.31446
T = 273.15 + temp_c
S = R * T * np.log(10) / F
act_fe2 = log_a_fe2 * S
act_fe3 = log_a_fe3 * S
G_H2O = -237130  # J/mol

# --- 標準生成ギブズエネルギー [J/mol] ---
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

# --- 計算グリッド（Cloud安定用に軽量化） ---
res = 300
ph_vec = np.linspace(0, 14, res)
e_vec = np.linspace(-2.5, 2.5, res)
PH, E = np.meshgrid(ph_vec, e_vec)

# --- Psi 計算関数 ---
def calc_psi(PH, E, phase_type):
    Psi = {}
    Psi["Fe"] = np.full_like(PH, Gf["Fe"] / F)
    Psi["Fe2+"] = Gf["Fe2+"] / F + act_fe2 - 2 * E
    Psi["Fe3+"] = Gf["Fe3+"] / F + act_fe3 - 3 * E
    Psi["HFeO2-"] = (Gf["HFeO2-"] - 2 * G_H2O) / F - 2 * E - 3 * S * PH + act_fe2

    if phase_type == "Hydroxides only":
        Psi["Fe(OH)2"] = (Gf["Fe(OH)2"] - 2 * G_H2O) / F - 2 * E - 2 * S * PH + act_fe2
        P
