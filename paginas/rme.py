import streamlit as st
import pandas as pd
from streamlit_apexjs import st_apexcharts
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards

from helpers import obtem_conexao, meses, DT_ATUALIZACAO

@st.cache_data
def busca_resultados(dias_letivos, ano):
    regional = pd.DataFrame.from_dict({
        'regional_id':[1,2,3,4,5,6,7,8,9],
        'regional':['BARREIRO','CENTRO SUL','LESTE','NORDESTE','NOROESTE','NORTE','OESTE','PAMPULHA','VENDA NOVA']
    })

    conn = obtem_conexao()

    sql_20 = '''
        select e.regional regional_id, count(fa.cod_aluno) _0_20
        from faltas_acumuladas fa, aluno a , escola e, turma t
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and t.cod_sequ_turm = a.cod_turm_atua
        and t.ensino in (7,8,9,10,11,12,13,14,15)
        and 100*(cast(fa.total_sem_jus as float)/%s) < 20.0
        group by e.regional
    '''%(ano, dias_letivos)

    data_menor_20 = conn.query(sql_20)

    sql_20_25 = '''
        select e.regional regional_id, count(fa.cod_aluno) _20_25
        from faltas_acumuladas fa, aluno a , escola e, turma t
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and t.cod_sequ_turm = a.cod_turm_atua
        and t.ensino in (7,8,9,10,11,12,13,14,15)        
        and 100*(cast(fa.total_sem_jus as float)/%s) >= 20.0
        and 100*(cast(fa.total_sem_jus as float)/%s) < 25.0
        group by e.regional
    '''%(ano, dias_letivos, dias_letivos)

    data_20_25 = conn.query(sql_20_25)

    sql_maior_25 = '''
        select e.regional regional_id, count(fa.cod_aluno) _25_100
        from faltas_acumuladas fa, aluno a , escola e, turma t
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and t.cod_sequ_turm = a.cod_turm_atua
        and t.ensino in (7,8,9,10,11,12,13,14,15)        
        and 100*(cast(fa.total_sem_jus as float)/%s) >= 25.0
        group by e.regional
    '''%(ano, dias_letivos)

    data_maior_25 = conn.query(sql_maior_25)

    result = regional.merge(data_menor_20, on='regional_id', how='left' )
    result = result.merge(data_20_25, on='regional_id', how='left')
    result = result.merge(data_maior_25, on='regional_id', how='left')

    result.fillna(0, inplace=True)

    result['total'] = result['_0_20'] + result['_20_25'] + result['_25_100']
    result['p_0_20'] = 100*result['_0_20']/result['total']
    result['p_20_25'] = 100*result['_20_25']/result['total']
    result['p_25_100'] = 100*result['_25_100']/result['total']

    return result


def rme(dias_letivos, ano, mes):
    st.header("Secretaria Municipal de Educação - PBH", divider='rainbow')
    st.subheader("Percentual de Alunos do Ensino Fundamental por Taxa de Infrequência na RME")
    st.write('Acumulado de Fevereiro à  %s de %s - Dias Letivos no período: %s - Dados atualizados em %s'%(meses[mes], ano, dias_letivos, DT_ATUALIZACAO))

    resultado = busca_resultados(dias_letivos, ano)

    total_0_20 = resultado['_0_20'].sum(axis=0)
    total_20_25 = resultado['_20_25'].sum(axis=0)
    total_25_100 = resultado['_25_100'].sum(axis=0)
    total = resultado['total'].sum(axis=0)

    #col1, col2, col3, col4 = st.columns(4)
    '''
    col1.metric(
                label='Menor ou igual à 10%', 
                value= str(round(100*(total_0_10/total), 1))+'%'
                )
    col2.metric(
                label='Entre 10% e 20%', 
                value=str(round(100*(total_10_20/total), 1))+'%'
                )
    '''
    col3, col4 = st.columns(2)
    col3.metric(
                label='Entre 20% e 25%', 
                value=str(round(100*(total_20_25/total), 1))+'%'
                )
    col4.metric(
                label='Maior ou igual à 25%', 
                value=str(round(100*(total_25_100/total), 1))+'%'
                )
    style_metric_cards()

    options = {
        'chart': {
          'type': 'bar',
          'height': 1000,
          'stacked': True,
          'stackType': '100%'
        },
        'colors': ['#1ED0DF', '#ffa500', "#ff0000"],
        'plotOptions': {
          'bar': {
            'horizontal': True,
          },
        },
        'stroke': {
          'width': 1,
          'colors': ['#fff']
        },
        'title': {
                'text': 'Percentual de Alunos do Ensino Fundamental por Taxa de Infrequência nas Regionais',
                'horizontalAlign': 'center',
        },
        'subtitle': {
                'text': 'Acumulado de Fevereiro à  %s de %s - Dias Letivos no período: %s'%(meses[mes], ano, dias_letivos),
        },  
        'xaxis': {
          'categories':  ['BARREIRO','CENTRO SUL','LESTE','NORDESTE','NOROESTE','NORTE','OESTE','PAMPULHA','VENDA NOVA'],
        },
        'legend': {
          'position': 'top',
          'horizontalAlign': 'center',
          'offsetX': 40
        }
    }
    series = [dict(name='Menor que 20%',data=resultado['p_0_20'].tolist()),
              dict(name='Entre 20% e 25%',data=resultado['p_20_25'].tolist()),
              dict(name='Maior ou igual à 25%',data=resultado['p_25_100'].tolist())]

    st_apexcharts(options, series, 'bar', 1100)    

    rename = {
        'regional':'Regional', 
        '_0_20':'Menor que 20%', 
        '_20_25':'Entre 20% e 25%', 
        '_25_100':'Maior ou igual à 25%', 
        'total':'Total'
    }
    
    df=resultado[['regional', '_0_20',  '_20_25', '_25_100', 'total']].rename(columns=rename)

    st.write('Total de Alunos do Ensino Fundamental por Taxa de Infrequência nas Regionais')
    st.dataframe(df, hide_index=True, use_container_width=True)


