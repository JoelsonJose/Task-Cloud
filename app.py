import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sabor do Sertão", layout="wide")
st.title("Painel de Vendas: Sabor do Sertão")

@st.cache_data
def carregar(arquivo):
    return pd.read_csv(arquivo, parse_dates=["data"])

arquivo = st.sidebar.file_uploader("Envie o CSV de vendas", type=["csv"])

if arquivo is None:
    st.info("Envie o arquivo para começar.")
    st.stop()

df = carregar(arquivo)

# ==============================================================================
# NÍVEL 3: FILTROS NA BARRA LATERAL
# ==============================================================================
st.sidebar.header("Filtros")

# Filtro de Cidade
cidades_disponiveis = df["cidade"].unique()
cidades_selecionadas = st.sidebar.multiselect(
    "Selecione as Cidades:",
    options=cidades_disponiveis,
    default=cidades_disponiveis
)

# Filtro de Categoria
categorias_disponiveis = df["categoria"].unique()
categorias_selecionadas = st.sidebar.multiselect(
    "Selecione as Categorias:",
    options=categorias_disponiveis,
    default=categorias_disponiveis
)

# Filtro de Intervalo de Datas
data_min = df["data"].min().date()
data_max = df["data"].max().date()

intervalo_datas = st.sidebar.date_input(
    "Selecione o Intervalo de Datas:",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

# Aplicação dos Filtros
if len(intervalo_datas) == 2:
    data_inicio, data_fim = intervalo_datas
    df_filtrado = df[
        (df["cidade"].isin(cidades_selecionadas)) &
        (df["categoria"].isin(categorias_selecionadas)) &
        (df["data"].dt.date >= data_inicio) &
        (df["data"].dt.date <= data_fim)
    ]
else:
    df_filtrado = df[
        (df["cidade"].isin(cidades_selecionadas)) &
        (df["categoria"].isin(categorias_selecionadas))
    ]

# ==============================================================================
# NÍVEL 1: EXPLORAÇÃO E TRATAMENTO DE DADOS
# ==============================================================================
st.header("Nível 1: Exploração e Tratamento de Dados")

# Tratamento dos dados ausentes na coluna 'avaliacao'
media_avaliacao = df_filtrado["avaliacao"].mean()
df_filtrado["avaliacao"] = df_filtrado["avaliacao"].fillna(media_avaliacao)

with st.expander("Visualizar Dados Brutos e Estatísticas"):
    st.subheader("Primeiras linhas do DataFrame")
    st.dataframe(df_filtrado.head())
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resumo Estatístico")
        st.dataframe(df_filtrado.describe())
    with col2:
        st.subheader("Valores Ausentes por Coluna")
        st.dataframe(df_filtrado.isnull().sum().rename("Qtd. Nulos"))

st.caption("Tratamento de dados ausentes: Os valores ausentes na coluna 'avaliacao' foram preenchidos com a média geral para manter o tamanho do conjunto de dados sem distorcer o comportamento médio do cliente.")

# ==============================================================================
# NÍVEL 2: INDICADORES (KPIs)
# ==============================================================================
st.header("Nível 2: Indicadores Principais")

faturamento_total = df_filtrado["total"].sum()
numero_vendas = len(df_filtrado)
ticket_medio = df_filtrado["total"].mean() if numero_vendas > 0 else 0
avaliacao_media = df_filtrado["avaliacao"].mean() if numero_vendas > 0 else 0

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
col_kpi1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
col_kpi2.metric("Número de Vendas", f"{numero_vendas:,}")
col_kpi3.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
col_kpi4.metric("Avaliação Média", f"{avaliacao_media:.2f} ⭐")

# ==============================================================================
# NÍVEL 4: GRÁFICOS ORGANIZADOS EM TABS
# ==============================================================================
st.header("Nível 4: Visualizações de Dados")

tab1, tab2, tab3, tab4, tab5, tab_bonus = st.tabs([
    "Faturamento Mensal", 
    "Faturamento por Cidade", 
    "Top Produtos", 
    "Formas de Pagamento", 
    "Mapa de Calor (Hora x Dia)",
    "Explorador Livre (Bônus)"
])

# 1. Faturamento Mensal (Linha)
with tab1:
    df_mensal = df_filtrado.copy()
    df_mensal["mes"] = df_mensal["data"].dt.to_period("M").astype(str)
    faturamento_mensal = df_mensal.groupby("mes")["total"].sum().reset_index()
    
    fig1 = px.line(
        faturamento_mensal, 
        x="mes", 
        y="total", 
        title="Faturamento Mensal (R$)",
        labels={"mes": "Mês", "total": "Faturamento (R$)"},
        markers=True
    )
    st.plotly_chart(fig1, use_container_width=True)

# 2. Faturamento por Cidade (Barras)
with tab2:
    faturamento_cidade = df_filtrado.groupby("cidade")["total"].sum().reset_index().sort_values("total", ascending=False)
    fig2 = px.bar(
        faturamento_cidade, 
        x="cidade", 
        y="total", 
        title="Faturamento Total por Cidade",
        labels={"cidade": "Cidade", "total": "Faturamento (R$)"},
        color="cidade"
    )
    st.plotly_chart(fig2, use_container_width=True)

# 3. Top 5 Produtos Mais Vendidos (Barras Horizontais)
with tab3:
    top_produtos = df_filtrado.groupby("produto")["quantidade"].sum().reset_index().sort_values("quantidade", ascending=True).tail(5)
    fig3 = px.bar(
        top_produtos, 
        x="quantidade", 
        y="produto", 
        orientation="h",
        title="Top 5 Produtos Mais Vendidos (Quantidade)",
        labels={"quantidade": "Quantidade Vendida", "produto": "Produto"},
        color="quantidade"
    )
    st.plotly_chart(fig3, use_container_width=True)

# 4. Formas de Pagamento (Pizza)
with tab4:
    pagamento = df_filtrado.groupby("pagamento")["total"].sum().reset_index()
    fig4 = px.pie(
        pagamento, 
        names="pagamento", 
        values="total", 
        title="Participação no Faturamento por Forma de Pagamento",
        hole=0.4
    )
    st.plotly_chart(fig4, use_container_width=True)

# 5. Opcional: Mapa de calor de vendas por dia da semana e hora
with tab5:
    df_mapa = df_filtrado.copy()
    df_mapa["dia_semana"] = df_mapa["data"].dt.day_name()
    
    fig5 = px.density_heatmap(
        df_mapa, 
        x="hora", 
        y="dia_semana", 
        z="total", 
        histfunc="sum",
        title="Mapa de Calor: Faturamento por Hora e Dia da Semana",
        labels={"hora": "Hora do Dia", "dia_semana": "Dia da Semana", "z": "Faturamento"}
    )
    st.plotly_chart(fig5, use_container_width=True)

# DESAFIO BÔNUS: Explorador livre
with tab_bonus:
    st.subheader("Explorador Livre de Dados")
    col_eixo_x, col_eixo_y, col_tipo = st.columns(3)
    
    com_colunas = df_filtrado.columns.tolist()
    
    with col_eixo_x:
        eixo_x = st.selectbox("Escolha o Eixo X:", com_colunas, index=com_colunas.index("cidade"))
    with col_eixo_y:
        eixo_y = st.selectbox("Escolha o Eixo Y:", com_colunas, index=com_colunas.index("total"))
    with col_tipo:
        tipo_grafico = st.selectbox("Tipo de Gráfico:", ["Barras", "Linha", "Dispersão (Scatter)"])
        
    if tipo_grafico == "Barras":
        fig_bonus = px.bar(df_filtrado, x=eixo_x, y=eixo_y)
    elif tipo_grafico == "Linha":
        fig_bonus = px.line(df_filtrado, x=eixo_x, y=eixo_y)
    else:
        fig_bonus = px.scatter(df_filtrado, x=eixo_x, y=eixo_y)
        
    st.plotly_chart(fig_bonus, use_container_width=True)

# ==============================================================================
# NÍVEL 5: INSIGHTS E EXPORTAÇÃO
# ==============================================================================
st.header("Nível 5: Insights do Gestor e Exportação")

st.markdown("""
### 💡 Insights Principais para Gestão
1. **Preferência de Pagamento:** O PIX e Cartões de Crédito representam a maior fatia do faturamento total, indicando que a infraestrutura de pagamentos digitais deve ser mantida sem falhas operacionais.
2. **Concentração por Cidade:** Recife e Olinda concentram o maior volume de vendas e faturamento, sugerindo foco de campanhas de marketing nessa região metropolitana.
3. **Pico de Consumo de Pratos Principais:** Os itens da categoria *Pratos* possuem o maior impacto no ticket médio da rede.
""")

# Botão para baixar o CSV filtrado
csv_filtrado = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar Dados Filtrados (CSV)",
    data=csv_filtrado,
    file_name="vendas_sabor_do_sertao_filtrado.csv",
    mime="text/csv"
)