import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
import io
import zipfile

import streamlit as st

# Função para verificar a senha
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""

    def password_entered():
        """Verifica se a senha na session state é a correta."""
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Não manter a senha em memória
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primeira execução, mostra o campo de senha.
        st.text_input(
            "Digite a senha para acessar:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Senha incorreta, mostra o campo novamente com uma mensagem de erro.
        st.text_input(
            "Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password"
        )
        st.error("Senha incorreta.")
        return False
    else:
        # Senha correta.
        return True

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---
if check_password():
    # TODO: Coloque todo o resto do seu código (st.title, st.file_uploader, etc.)
    # aqui dentro deste "if".

    st.set_page_config(layout="wide", page_title="Gerador de Roadmap")
    st.title("Gerador de Roadmaps a partir de CSV")
    # ... resto do seu código ...

# --- A MAIORIA DAS FUNÇÕES ORIGINAIS PERMANECE A MESMA ---

# Define o fuso horário de Brasília
try:
    TZ = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    TZ = pytz.timezone('Etc/GMT+3')

TODAY = datetime.now(TZ).date()

# Mapeamento de meses para português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Mapeamentos de estilo (cores para status, esforço e risco)
STATUS_COLORS = {
    'BACKLOG': ('bg-blue-500', 'border-blue-500'),
    'Concluido': ('bg-green-500', 'border-green-500'),
    'Discover': ('bg-gray-500', 'border-gray-500'),
    'Em análise': ('bg-purple-500', 'border-purple-500'),
    'Em andamento': ('bg-yellow-500', 'border-yellow-500'),
    'Em homologação': ('bg-cyan-500', 'border-cyan-500'),
    'Tarefas pendentes': ('bg-red-500', 'border-red-500'),
    'Default': ('bg-gray-400', 'border-gray-400')
}

ESFORCO_COLORS = {
    'Evolução': 'bg-green-200 text-green-800',
    'Sustentação': 'bg-indigo-200 text-indigo-800',
    'SETUP': 'bg-orange-200 text-orange-800',
    'Default': 'bg-gray-200 text-gray-800'
}

RISK_LEGEND = {
    "Concluído": "bg-green-100",
    "Atrasado": "bg-red-100",
    "Próximos 10 dias": "bg-yellow-100",
    "Futuro (>10 dias)": "bg-blue-100"
}

def load_and_clean_data(uploaded_file):
    # Modificada para ler um arquivo enviado via upload em vez de um caminho
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        df.rename(columns={'chave': 'chave', 'resumo': 'resumo', 'emissor': 'emissor',
                           'tipo_de_item': 'tipo_item', 'conta_de_esforço': 'conta_esforco',
                           'status': 'status', 'data_limite': 'data_limite', 'data_real': 'data_real'}, inplace=True)
        df.dropna(subset=['chave'], inplace=True)
        df['data_limite_dt'] = pd.to_datetime(df['data_limite'], errors='coerce').dt.tz_localize(TZ)
        df['data_real_dt'] = pd.to_datetime(df['data_real'], errors='coerce').dt.tz_localize(TZ)
        df['status'] = df['status'].str.strip().replace('Concluído', 'Concluido')
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo CSV: {e}")
        return None

# ... (As funções create_card_html, create_list_item_html, create_legends_html permanecem exatamente as mesmas) ...
def create_card_html(item, is_roadmap=False):
    """Gera o HTML para um único CARD de item (usado no Roadmap)."""
    status_bg, status_border = STATUS_COLORS.get(item.get('status', 'Default'), STATUS_COLORS['Default'])
    esforco_color = ESFORCO_COLORS.get(item.get('conta_esforco', 'Default'), ESFORCO_COLORS['Default'])
    card_bg_color = get_risk_color_class(item) if is_roadmap else 'bg-white'

    display_date_html = ''
    if pd.notna(item.get('data_real_dt')):
        display_date_html = f'<p class="text-sm font-bold text-gray-600">{item["data_real_dt"].day}</p>'
    elif is_roadmap and pd.notna(item.get('data_limite_dt')):
        display_date_html = f'<p class="text-sm font-bold text-gray-600">{item["data_limite_dt"].day}</p>'
    
    completion_date_html = ''
    if item.get('status') == 'Concluido' and pd.notna(item.get('data_real_dt')):
        formatted_date = item['data_real_dt'].strftime('%d/%m/%Y')
        completion_date_html = f'<p class="text-xs text-gray-500 mt-1">Concluído em: {formatted_date}</p>'

    return f"""
    <div class="p-4 rounded-lg shadow-md border-l-4 {status_border} {card_bg_color} flex flex-col h-full">
        <div>
            <div class="flex justify-between items-start">
                <p class="font-bold text-lg text-gray-800">{item.get('chave', 'N/A')}</p>
                {display_date_html}
            </div>
            {completion_date_html}
        </div>
        <p class="text-sm text-gray-700 my-2 flex-grow">{item.get('resumo', 'N/A')}</p>
        <div class="mt-auto flex items-center flex-wrap gap-2 pt-2">
            <span class="text-xs font-semibold px-2 py-1 rounded-full bg-gray-200 text-gray-800">{item.get('tipo_item', 'N/A')}</span>
            <span class="text-xs font-semibold px-2 py-1 rounded-full {esforco_color}">{item.get('conta_esforco', 'N/A')}</span>
            <span class="text-xs font-semibold px-2 py-1 rounded-full text-white {status_bg}">{item.get('status', 'N/A')}</span>
        </div>
    </div>
    """
def get_risk_color_class(item):
    """Determina a cor de fundo do card com base no status e data limite."""
    if item['status'] == 'Concluido':
        return RISK_LEGEND['Concluído']
    
    if pd.isna(item['data_limite_dt']):
        return 'bg-white'
    
    limite_date = item['data_limite_dt'].date()
    if limite_date < TODAY:
        return RISK_LEGEND['Atrasado']
    
    delta_days = (limite_date - TODAY).days
    if delta_days <= 10:
        return RISK_LEGEND['Próximos 10 dias']
    
    return RISK_LEGEND['Futuro (>10 dias)']

def create_list_item_html(item):
    """Gera o HTML para um item em formato de LISTA (usado no Backlog)."""
    status_bg, status_border = STATUS_COLORS.get(item.get('status', 'Default'), STATUS_COLORS['Default'])
    esforco_color = ESFORCO_COLORS.get(item.get('conta_esforco', 'Default'), ESFORCO_COLORS['Default'])

    completion_date_html = ''
    if item.get('status') == 'Concluido' and pd.notna(item.get('data_real_dt')):
        formatted_date = item['data_real_dt'].strftime('%d/%m/%Y')
        completion_date_html = f'<span class="text-sm text-gray-600">{formatted_date}</span>'

    return f"""
    <tr class="border-t border-gray-200 bg-white">
        <td class="p-3 border-l-4 {status_border}" style="width: 50%;">
            <p class="font-bold text-gray-800">{item.get('chave', 'N/A')}</p>
            <p class="text-sm text-gray-600">{item.get('resumo', 'N/A')}</p>
        </td>
        <td class="p-3 align-middle text-center">
            <span class="text-xs font-semibold px-2 py-1 rounded-full text-white {status_bg}">{item.get('status', 'N/A')}</span>
        </td>
        <td class="p-3 align-middle text-center">
            <span class="text-xs font-semibold px-2 py-1 rounded-full {esforco_color}">{item.get('conta_esforco', 'N/A')}</span>
        </td>
        <td class="p-3 align-middle text-center">
            <span class="text-xs font-semibold px-2 py-1 rounded-full bg-gray-200 text-gray-800">{item.get('tipo_item', 'N/A')}</span>
        </td>
        <td class="p-3 align-middle text-center">
            {completion_date_html}
        </td>
    </tr>
    """

def create_legends_html():
    """Gera o HTML para as legendas de risco e status."""
    risk_legend_html = ''.join([f'<div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full {color} border border-gray-300"></div><span>{name}</span></div>'
                              for name, color in RISK_LEGEND.items()])
    status_legend_html = ''.join([f'<div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full {bg}"></div><span>{status}</span></div>'
                                for status, (bg, _) in STATUS_COLORS.items() if status != 'Default'])
    
    return f"""
    <div class="mt-8 pt-4 border-t-2">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
                <h3 class="font-bold text-lg mb-4">Legenda de Risco</h3>
                <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">{risk_legend_html}</div>
            </div>
            <div>
                <h3 class="font-bold text-lg mb-4">Legenda de Status</h3>
                <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">{status_legend_html}</div>
            </div>
        </div>
    </div>
    """

def generate_issuer_content_html(df_issuer):
    """Gera o conteúdo HTML (roadmap e backlog) para um único emissor."""
    emissor = df_issuer['emissor'].iloc[0]

    # SLIDE 1: ROADMAP DE ENTREGÁVEIS (ITENS COM DATA LIMITE)
    planned_items = df_issuer[df_issuer['data_limite_dt'].notna()].sort_values(by='data_limite_dt')
    timeline_html = ""
    if not planned_items.empty:
        grouped = planned_items.groupby([planned_items['data_limite_dt'].dt.year.rename('year'),
                                         planned_items['data_limite_dt'].dt.month.rename('month')])
        
        timeline_html += '<div class="flex space-x-8">'
        for (year, month), group in grouped:
            month_name = MESES_PT.get(month, '')
            cards_html = "".join([create_card_html(item, is_roadmap=True) for _, item in group.iterrows()])
            timeline_html += f"""
            <div class="flex-shrink-0 w-80">
                <div class="text-center py-2 px-4 rounded-lg bg-gray-700 text-white font-bold mb-4">{month_name} {year}</div>
                <div class="space-y-4">{cards_html}</div>
            </div>
            """
        timeline_html += '</div>'
    else:
        timeline_html = "<p class='text-gray-500'>Nenhum item planejado para este emissor.</p>"

    # SLIDE 2: FILA DE ITENS NÃO PLANEJADOS (FORMATO DE LISTA)
    unplanned_items = df_issuer[df_issuer['data_limite_dt'].isna()]
    
    # Cabeçalho da Tabela
    table_header = """
    <thead class="bg-gray-50">
        <tr>
            <th class="p-3 text-left text-sm font-semibold text-gray-500 uppercase tracking-wider" style="width: 50%;">Chave e Resumo</th>
            <th class="p-3 text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">Status</th>
            <th class="p-3 text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">Conta de Esforço</th>
            <th class="p-3 text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">Tipo de Item</th>
            <th class="p-3 text-center text-sm font-semibold text-gray-500 uppercase tracking-wider">Data Conclusão</th>
        </tr>
    </thead>
    """

    def generate_table_section(items_df):
        """Função interna para gerar uma seção da tabela com scroll, se necessário."""
        if items_df.empty:
            return "<p class='text-gray-500 px-2'>Nenhum item nesta seção.</p>"
        
        # Lógica de Scroll Vertical
        scroll_style = 'max-height: 450px; overflow-y: auto;' if len(items_df) > 10 else ''
        
        table_body = "".join([create_list_item_html(item) for _, item in items_df.iterrows()])
        
        return f"""
        <div class="border rounded-lg" style="{scroll_style}">
            <table class="w-full table-fixed">
                {table_header}
                <tbody>
                    {table_body}
                </tbody>
            </table>
        </div>
        """

    items_aberto = unplanned_items[unplanned_items['status'] != 'Concluido']
    aberto_html = generate_table_section(items_aberto)
        
    items_concluido = unplanned_items[unplanned_items['status'] == 'Concluido']
    concluido_html = generate_table_section(items_concluido)

    unplanned_html = f"""
    <div>
        <h3 class="text-xl font-bold text-gray-700 mb-4 pb-2 border-b-2">Itens em Aberto</h3>
        {aberto_html}
    </div>
    <div class="mt-10">
        <h3 class="text-xl font-bold text-gray-700 mb-4 pb-2 border-b-2">Itens Concluídos</h3>
        {concluido_html}
    </div>
    """
    return f"""
    <div class="presentation-slide">
        <h1 class="text-3xl font-bold text-gray-800">Roadmap de Entregáveis - {emissor}</h1>
        <h2 class="text-xl text-gray-600 mb-8">Visão de Entregas Planejadas para 2025</h2>
        <div class="overflow-x-auto pb-4">{timeline_html}</div>
        {create_legends_html()}
    </div>
    <div class="presentation-slide">
        <h1 class="text-3xl font-bold text-gray-800">Fila de Itens Não Planejados/Sustentação - {emissor}</h1>
        <h2 class="text-xl text-gray-600 mb-8">Demandas que competem pela capacidade da equipe.</h2>
        {unplanned_html}
    </div>
    """

def wrap_with_html_shell(content, title):
    """Envolve o conteúdo gerado com a estrutura HTML base."""
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #f0f4f8; }}
        .presentation-slide {{ 
            background-color: white; 
            padding: 2rem; 
            border-radius: 0.5rem; 
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); 
            margin-bottom: 2rem; 
        }}
    </style>
</head>
<body class="p-8">
    {content}
</body>
</html>
    """

# --- LÓGICA DA APLICAÇÃO WEB COM STREAMLIT ---

st.set_page_config(layout="wide", page_title="Gerador de Roadmap")

st.title("Gerador de Roadmaps a partir de CSV")

st.write(
    "Faça o upload do seu arquivo CSV para gerar os relatórios de roadmap. "
    "O arquivo deve conter as colunas: Emissor, Chave, Resumo, Status, Data limite, etc."
)

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=['csv'])

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)

    if df is not None:
        st.success("Arquivo CSV carregado e processado com sucesso!")

        emissores = df['emissor'].dropna().unique()

        # Cria um arquivo ZIP em memória para armazenar os relatórios
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            # Gera e adiciona o relatório unificado
            all_emissor_html = ""
            for emissor in emissores:
                df_emissor = df[df['emissor'] == emissor].copy()
                all_emissor_html += generate_issuer_content_html(df_emissor)
            
            final_unified_html = wrap_with_html_shell(all_emissor_html, "Roadmap Geral de Entregáveis")
            zip_file.writestr("roadmap_geral.html", final_unified_html.encode('utf-8'))

            # Gera e adiciona os relatórios individuais
            for emissor in emissores:
                df_emissor = df[df['emissor'] == emissor].copy()
                emissor_content = generate_issuer_content_html(df_emissor)
                final_html = wrap_with_html_shell(emissor_content, f"Roadmap - {emissor}")
                file_name = f"roadmap_{emissor.replace(' ', '_').lower()}.html"
                zip_file.writestr(file_name, final_html.encode('utf-8'))

        # Posiciona o buffer no início para a leitura
        zip_buffer.seek(0)

        # Cria o botão de download
        st.download_button(
            label="Baixar todos os relatórios (.zip)",
            data=zip_buffer,
            file_name="roadmaps.zip",
            mime="application/zip",
        )
        
        # Oferece uma prévia do primeiro relatório na própria página
        st.subheader("Prévia do Relatório Geral")
        st.components.v1.html(final_unified_html, height=600, scrolling=True)