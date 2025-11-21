import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard de Leads - Cosméticos", layout="wide", page_icon="📊")

# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data # Isso faz o dashboard ficar rápido, não recarrega o CSV a cada clique
def carregar_dados():
    # Procura todos os arquivos que começam com o padrão definido
    arquivos = glob.glob("Cosmeticos_ATIVAS_*.csv")
    
    if not arquivos:
        return None
    
    lista_dfs = []
    for arquivo in arquivos:
        # Lê cada arquivo
        df_temp = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', dtype=str)
        
        # Adiciona uma coluna identificando a origem (Fixo ou Celular) baseado no nome do arquivo
        tipo = "Celular" if "CELULAR" in arquivo.upper() else "Fixo"
        if "OUTROS" in arquivo.upper(): tipo = "Outros"
        df_temp['Tipo_Contato'] = tipo
        
        lista_dfs.append(df_temp)
    
    # Junta tudo num tabelão só
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        return df_final
    return None

# --- INTERFACE PRINCIPAL ---
st.title("📊 Dashboard de Leads: Setor de Cosméticos")
st.markdown("Visão estratégica da base de dados extraída da Receita Federal.")

df = carregar_dados()

if df is not None:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Estado (UF) - Extrai do CSV (assumindo que a coluna UF existe)
    # Se sua base não tiver coluna 'UF', o script tentará extrair, senão avisa.
    if 'UF' in df.columns:
        estados = df['UF'].unique()
        estados_selecionados = st.sidebar.multiselect("Filtrar por Estado (UF):", options=estados, default=estados)
        df_filtrado = df[df['UF'].isin(estados_selecionados)]
    else:
        st.warning("Coluna 'UF' não encontrada. Mostrando todos os dados.")
        df_filtrado = df

    # --- KPIs (NUMEROS GRANDES) ---
    col1, col2, col3 = st.columns(3)
    
    total_leads = len(df_filtrado)
    total_celular = len(df_filtrado[df_filtrado['Tipo_Contato'] == 'Celular'])
    total_fixo = len(df_filtrado[df_filtrado['Tipo_Contato'] == 'Fixo'])
    
    col1.metric("Total de Leads Qualificados", f"{total_leads:,.0f}")
    col2.metric("Contatos Celular (WhatsApp)", f"{total_celular:,.0f}", delta_color="normal")
    col3.metric("Contatos Fixo", f"{total_fixo:,.0f}")

    st.divider()

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Distribuição por Estado")
        if 'UF' in df_filtrado.columns:
            contagem_uf = df_filtrado['UF'].value_counts().reset_index()
            contagem_uf.columns = ['UF', 'Quantidade']
            fig_bar = px.bar(contagem_uf, x='UF', y='Quantidade', color='Quantidade', 
                             color_continuous_scale='Blues', title="Concentração de Empresas por UF")
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_graf2:
        st.subheader("Fixo vs Celular")
        contagem_tipo = df_filtrado['Tipo_Contato'].value_counts().reset_index()
        contagem_tipo.columns = ['Tipo', 'Quantidade']
        fig_pie = px.pie(contagem_tipo, values='Quantidade', names='Tipo', 
                         title="Proporção da Base de Contatos", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.subheader("🔍 Explorar Base de Dados")
    st.dataframe(df_filtrado, use_container_width=True, height=400)

    # --- BOTÃO DE DOWNLOAD DA SELEÇÃO ---
    # Permite baixar apenas o que foi filtrado na tela
    csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 Baixar CSV dos Dados Filtrados na Tela",
        data=csv,
        file_name="leads_filtrados_dashboard.csv",
        mime="text/csv",
    )

else:
    st.error("Nenhum arquivo CSV encontrado! Certifique-se que os arquivos 'Cosmeticos_ATIVAS_...' estão na mesma pasta.")
    st.info("Rode os scripts de extração anteriores primeiro.")