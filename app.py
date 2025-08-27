import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
import io
import zipfile

# --- PASSO 1: CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config() deve ser o primeiro comando Streamlit do script.
st.set_page_config(layout="wide", page_title="Gerador de Roadmap")

# --- PASSO 2: DEFINIÇÃO DE CONSTANTES E FUNÇÕES AUXILIARES ---

# Define o fuso horário de Brasília
try:
    TZ = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    TZ = pytz.timezone('Etc/GMT+3')

TODAY = datetime.now(TZ).date()

# Mapeamentos (MESES, CORES, etc.)
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
STATUS_COLORS = {
    'BACKLOG': ('bg-blue-500', 'border-blue-500'), 'Concluido': ('bg-green-500', 'border-green-500'),
    'Discover': ('bg-gray-500', 'border-gray-500'), 'Em análise': ('bg-purple-500', 'border-purple-500'),
    'Em andamento': ('bg-yellow-500', 'border-yellow-500'), 'Em homologação': ('bg-cyan-500', 'border-cyan-500'),
    'Tarefas pendentes': ('bg-red-500', 'border-red-500'), 'Default': ('bg-gray-400', 'border-gray-400')
}
ESFORCO_COLORS = {
    'Evolução': 'bg-green-200 text-green-800', 'Sustentação': 'bg-indigo-200 text-indigo-800',
    'SETUP': 'bg-orange-200 text-orange-800', 'Default': 'bg-gray-200 text-gray-800'
}
RISK_LEGEND = {
    "Concluído": "bg-green-100", "Atrasado": "bg-red-100", "Próximos 10 dias": "bg-yellow-100",
    "Futuro (>10 dias)": "bg-blue-100"
}

# Todas as suas funções de lógica (load_and_clean_data, create_card_html, etc.)
# podem ser definidas aqui. Elas não mudaram.

def load_and_clean_data(uploaded_file):
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

def get_risk_color_class(item):
    if item['status'] == 'Concluido': return RISK_LEGEND['Concluído']
    if pd.isna(item['data_limite_dt']): return 'bg-white'
    limite_date = item['data_limite_dt'].date()
    if limite_date < TODAY: return RISK_LEGEND['Atrasado']
    delta_days = (limite_date - TODAY).days
    if delta_days <= 10: return RISK_LEGEND['Próximos 10 dias']
    return RISK_LEGEND['Futuro (>10 dias)']

def create_card_html(item, is_roadmap=False):
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
    return f"""<div class="p-4 rounded-lg shadow-md border-l-4 {status_border} {card_bg_color} flex flex-col h-full"><div><div class="flex justify-between items-start"><p class="font-bold text-lg text-gray-800">{item.get('chave', 'N/A')}</p>{display_date_html}</div>{completion_date_html}</div><p class="text-sm text-gray-700 my-2 flex-grow">{item.get('resumo', 'N/A')}</p><div class="mt-auto flex items-center flex-wrap gap-2 pt-2"><span class="text-xs font-semibold px-2 py-1 rounded-full bg-gray-200 text-gray-800">{item.get('tipo_item', 'N/A')}</span><span class="text-xs font-semibold px-2 py-1 rounded-full {esforco_color}">{item.get('conta_esforco', 'N/A')}</span><span class="text-xs font-semibold px-2 py-1 rounded-full text-white {status_bg}">{item.get('status', 'N/A')}</span></div></div>"""

def create_list_item_html(item):
    status_bg, status_border = STATUS_COLORS.get(item.get('status', 'Default'), STATUS_COLORS['Default'])
    esforco_color = ESFORCO_COLORS.get(item.get('conta_esforco', 'Default'), ESFORCO_COLORS['Default'])
    completion_date_html = ''
    if item.get('status') == 'Concluido' and pd.notna(item.get('data_real_dt')):
        formatted_date = item['data_real_dt'].strftime('%d/%m/%Y')
        completion_date_html = f'<span class="text-sm text-gray-600">{formatted_date}</span>'
    return f"""<tr class="border-t border-gray-200 bg-white"><td class="p-3 border-l-4 {status_border}" style="width: 50%;"><p class="font-bold text-gray-800">{item.get('chave', 'N/A')}</p><p class="text-sm text-gray-600">{item.get('resumo', 'N/A')}</p></td><td class="p-3 align-middle text-center"><span class="text-xs font-semibold px-2 py-1 rounded-full text-white {status_bg}">{item.get('status', 'N/A')}</span></td><td class="p-3 align-middle text-center"><span class="text-xs font-semibold px-2 py-1 rounded-full {esforco_color}">{item.get('conta_esforco', 'N/A')}</span></td><td class="p-3 align-middle text-center"><span class="text-xs font-semibold px-2 py-1 rounded-full bg-gray-200 text-gray-800">{item.get('tipo_item', 'N/A')}</span></td><td class="p-3 align-middle text-center">{completion_date_html}</td></tr>"""

def create_legends_html():
    risk_legend_html = ''.join([f'<div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full {color} border border-gray-300"></div><span>{name}</span></div>' for name, color in RISK_LEGEND.items()])
    status_legend_html = ''.join([f'<div class="flex items-center gap-2"><div class="w-4 h-4 rounded-full {bg}"></div><span>{status}</span></div>' for status, (bg, _) in STATUS_COLORS.items() if status != 'Default'])
    return f"""<div class="mt-8 pt-4 border-t-2"><div class="grid grid-cols-1 md:grid-cols-2 gap-8"><div><h3 class="font-bold text-lg mb-4">Legenda de Risco</h3><div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">{risk_legend_html}</div></div><div><h3 class="font-bold text-lg mb-4">Legenda de Status</h3><div class="flex flex-wrap gap-x-6 gap-y-2 text-sm">{status_legend_html}</div></div></div></div>"""

def generate_issuer_content_html(df_issuer):
    emissor = df_issuer['emissor'].iloc[0]
    planned_items = df_issuer[df_issuer['data_limite_dt'].notna()].sort_values(by='data_limite_dt')
    timeline_html = ""
    if not planned_items.empty:
        grouped = planned_items.groupby([planned_items['data_limite_dt'].dt.year.rename('year'), planned_items['data_limite_dt'].dt.month.rename('month')])
        timeline_html += '<div class="flex space-x-8">'
        for (year, month), group in grouped:
            month_name = MESES_PT.get(month, '')
            cards_html = "".join([create_card_html(item, is_roadmap=True) for _, item in group.iterrows()])
            timeline_html += f"""<div class="flex-shrink-0