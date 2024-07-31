import sys
sys.path.insert(0, 'modules')
#-----------------------------------------------------
import streamlit as st
from reccomendation_module import *

st.markdown("# Персональні рекомендації")
st.sidebar.markdown("# Персональні рекомендації")
#-----------------------------------------------------
import time
import hydralit_components as hc
    
if 'inac' not in st.session_state or st.session_state['inac'] is False: inac = False
else: inac = True

if inac:
    saves = get_saves(st.session_state['id'])
    if saves:
        # pick special content
        reccoms = remove_if_used(remove_duplicates(get_top_rated_films(count_genre_occurrences(saves))), saves)
        proporsions = sort_and_limit_dict(reccoms)
        # pick clustering content
        analysis = users_analysis()[st.session_state['gender']]
        clusters_analysis = cluster_users(analysis)
        ids = clustering_analysis(st.session_state['id'], clusters_analysis)

selected_option = st.selectbox("Дивитися рекомендації ", ["Спеціально для вас", "Також шукають"], index=0)
special_cont, similiar_cont = st.expander("Спеціально для вас", expanded=True), st.expander("Також шукають", expanded=True)  
if selected_option == "Спеціально для вас":
    if not inac: 
        with special_cont: st.write('Спочатку необхідно увійти в акаунт')
    elif not saves: 
        with special_cont: st.write('Добавте декілька фільмів у обране, щоб ми могли підібрати для Вас щось цікаве')
    else:  
        with special_cont: 
            keys = list(reccoms.keys())
            for i in range(len(keys)):
                show_reccomendations(reccoms[keys[i]][:proporsions[i]])
else:
    if not inac: 
        with similiar_cont: st.write('Спочатку необхідно увійти в акаунт')
    elif not saves:
        with similiar_cont: st.write('Добавте декілька фільмів у обране, щоб ми могли підібрати для Вас щось цікаве')    
    else:
        with similiar_cont:
            show_reccomendations(ids)
