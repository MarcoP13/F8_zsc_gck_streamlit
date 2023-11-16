import os
import pickle
# import pathlib
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth

import pandas as pd
import datetime

from panoply_loader import *

import plotly.express as px
import plotly.graph_objects as go

hide_st_style = """
            <style>
            #MainMenu { visibility: visible; }
            header { visibility: visible; }
            footer { visibility: hidden; }
            .css-10pw50.ea3mdgi1 { visibility: hidden; }
            .block-container.css-z5fcl4.ea3mdgi4 {
                padding-top: 0px !important;
                padding-left: 15px !important;
                padding-right: 10px !important;
            }
            footer:before{
                content:"Created by Force8 - 2023";
                display:block;
                position:relativ;
                bottom:0px;
            }
            .st-emotion-cache-z3au9t.a3mdgi2 {
                visibility: hidden;
            }
            </style>
            """  


def split_df_by_test(df_final_players):
    """Splits the given dataframe into separate dataframes for each test.
    Args: df_final_players: The dataframe to split.
    Returns: A dictionary of dataframes, where the keys are the test names and the values
        are the corresponding dataframes.
    """
    tests = df_final_players['text'].unique()
    df_dict = {}
    for test in tests:
        df_dict[test] = df_final_players[df_final_players['text'] == test]
    return df_dict

def split_df_by_player(df_final_players):
    tests = df_final_players['name'].unique()
    tests.sort()
    df_dict = {}
    for name in tests:
        df_dict[name] = df_final_players[df_final_players['name'] == name]
    return df_dict

def clean_df(df):
    # get rid of all 0 values
    df = df.loc[df['test_result']!=0]
    df['text'] = df['text'].replace(['"', "'"], "", regex=True)
    df['date'] = pd.to_datetime(df['date'])
    # df['day'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df = df.assign(year_month=lambda x: x['year'].astype(str) + '-' + x['month'].astype(str))
    # df['year_month'] = pd.to_datetime(df['year_month'], format='%Y-%m').dt.floor('D')
    df = df.rename(columns={'year_month': 'year month'})
    
    # Creating the 'year_month' column based on the 'date' column
    df['period'] = df['date'].dt.to_period('M')
    df = df.sort_values(by='period')
    return df


# # ************************************************************************************************************
# Page config 
# ****
st.set_page_config(
    layout="wide", 
    page_title="GCK/ZSC Lions", 
    page_icon=":ice_hockey_stick_and_puck:"
    )

# hide the hamburger and the modify the footer
st.markdown(hide_st_style, unsafe_allow_html=True)

names = ["Martin Kierot", "Force8 Coach", "General Access" ]
usernames = ["mkierot", "f8c", "gaccess"]

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)
    
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "test_dashboard", "zscgck", cookie_expiry_days=30)

# st.sidebar.image("logo.jpeg", use_column_width=True)
user_name, authentication_status, username = authenticator.login("Login",  "sidebar")
if authentication_status == False:
    st.error("Username/Password is incorrect")
if authentication_status == None:
    st.warning("Please enter your username and password")
if authentication_status:
    authenticator.logout("Logout", "sidebar")
    
    # # ************************************************************************************************************
    # load db files
    # ****
    df_season = load_season()
    df_agegroup = fetch_agegroup()
    df_agegroup_club = fetch_club_agegroup()
    df_teams = fetch_teams()
    df_team_players = fetch_team_players()
    df_player = fetch_players()
    df_batteries_template = fetch_batteries_template()
    df_batterie_names = df_batteries_template[['id_battery', 'name_battery']]
    df_batteries_players = fetch_batteries_players()
    df_testsexercises = fetch_testsexercises()
    df_exercise_info = fetch_exercise_info()
    df_testsexercises_results = fetch_testsexercises_results()
    
    # # ************************************************************************************************************
    # # Dataframe preparation
    # # ****  
    df_teams = pd.merge(df_teams, df_season, on='id_season')
    df_teams = pd.merge(df_teams, df_agegroup, on='id_agegroup')
    df_teams['team_name'] = df_teams['name'] + ' ' + df_teams['team_name']
    df_teams.drop(['name'], axis=1, inplace=True)
    df_team_players = pd.merge(df_team_players, df_season, on='id_season')
    df_testresults_players = pd.merge(df_testsexercises_results, df_exercise_info, on='id_testexercise')
    df_test_dates = df_batteries_players[['id_test_battery', 'date']]
    df_test_dates = df_test_dates.rename(columns={'id_test_battery': 'id_clubtest_result'})
    df_testresults_players = pd.merge(df_testresults_players, df_test_dates, on='id_clubtest_result')

    df_merged = pd.merge(df_batteries_players, df_batteries_template, on='id_battery')
    df_merged = pd.merge(df_merged, df_player, on='id_player')
    df_merged = pd.merge(df_merged, df_season, on='id_season')
    df_merged.drop(['id_user_x', 'id_user_y'], axis=1, inplace=True)

    df_batteries_total = df_merged.copy()
    df_batteries_total.drop(['id_season','id_player','id_season_battery','id_agegroup_battery','created_battery',], axis=1, inplace=True)

    df_battery_tests = pd.merge(df_testsexercises, df_exercise_info, on='id_testexercise')
    df_battery_tests.rename(columns={'id_clubtest': 'id_battery'}, inplace=True)
    df_battery_tests = pd.merge(df_battery_tests, df_batteries_template, on='id_battery')
    df_battery_tests = df_battery_tests.reindex(columns=['id_battery','name_battery','description_battery','id_testexercise','text','unit','description','id_user'])
    

    df_all_test = pd.merge(df_testresults_players, df_player, on='id_player')
    df_all_test.drop(['id_player','id_testexercise'], axis=1, inplace=True)
    df_final = df_all_test.copy()
    df_final.rename(columns={'id_clubtest': 'id_battery'}, inplace=True)
    df_final = pd.merge(df_final,df_batterie_names, on='id_battery')
    df_final = df_final.reindex(columns=['id_battery','name_battery','date','text','description','unit','test_result','comment','gender','dob','nationality','pos','name','id_user','id_agegroup_test','id_season'])
    df_final['date'] = pd.to_datetime(df_final['date']).dt.date
    df_final['dob'] = pd.to_datetime(df_final['dob']).dt.date
    df_final['test_result'] = df_final['test_result'].astype(float)
    
    # # ************************************************************************************************************
    # # SIDEBAR
    # # ****
    today = datetime.date.today()
    # last_month = today - datetime.timedelta(days=30)
    # last_year = today - datetime.timedelta(days=1095)
    date_min_test = df_final['date'].min()
    date_max_test = df_final['date'].max()
    selected_start = st.sidebar.date_input("Start date", value=date_min_test, min_value=date_min_test, max_value=date_max_test)
    selected_end = st.sidebar.date_input("End date", value=date_max_test, min_value=date_min_test, max_value=date_max_test)
    df_final = df_final[df_final["date"].between(selected_start, selected_end)]
    # Radiobuttons for the different views
    option = st.sidebar.radio('', ['Players Results', 'Selected Tests', 'Selected Batteries', 'General', 'CSV Export'])
    # select the season and the teams where we have test results
    season_names = df_season['season'].unique()
    season_names.sort()
    selected_season = st.sidebar.selectbox("Season ", season_names, key='season')
    df_agegroup = df_agegroup.loc[df_agegroup['id_agegroup'].isin(df_agegroup_club['id_agegroup'])]
    agegroup = df_agegroup['name'].unique()
    selected_agegroup = st.sidebar.selectbox("Agegroup ", agegroup, key='agegroup')
    selected_agegroup_id = df_agegroup.loc[df_agegroup['name'] == selected_agegroup, 'id_agegroup'].values[0]
    df_season_teams = df_teams.loc[(df_teams['season'] == selected_season) & (df_teams['id_agegroup'] == selected_agegroup_id)]
    selected_team_name = st.sidebar.selectbox('Team', df_season_teams['team_name'])
    selected_team_id = df_teams.loc[(df_teams['season'] == selected_season) & (df_teams['team_name'] == selected_team_name), 'id'].values[0]
    player_names = df_final["name"].unique()
    player_names.sort()
    # st.write(f"agegroup id = {selected_agegroup_id} | team id = {selected_team_id}")
    df_team_players = df_team_players.loc[df_team_players['id_team'] == selected_team_id] 
    df_selected_team_players = df_player.loc[df_player['id_player'].isin(df_team_players['id_player'])]
    df_selected_team_players = df_selected_team_players.loc[df_selected_team_players['name'].isin(player_names)]
    df_selected_team_players = df_selected_team_players['name'].tolist()
    df_selected_team_players.sort()
    try:
        selected_players = st.sidebar.multiselect("Players", player_names, df_selected_team_players, key='name')    
        if selected_players is None:
            selected_players = []
    except:
        st.subheader("Please select a team or a player to see the player results")
    
    try:
        df_final_players = df_final[df_final['name'].isin(selected_players)]
    except Exception as e:
        df_final_players = []
    
    # Refresh Button
    refresh_button = st.sidebar.button("Show results")
    if refresh_button:
        # st.experimental_rerun()
        st.rerun()
        
    try:
        df_final_players = df_final_players.reindex(columns=['name','date','text','test_result','unit','gender','dob','pos','nationality'])
        df_final_players['text'] = df_final_players['text'].replace(['"', "'"], "", regex=True)
        df_final_players['test_result'] = df_final_players['test_result'].replace(',', ".", regex=True)
    except:
        df_final_players = pd.DataFrame()  
    
    # # ************************************************************************************************************
    # # Display the page
    # # ****
    
    with st.expander("Filters", expanded=True):  
        
        col1, col2 = st.columns(2)   
        with col1: 
            st.info(f"Selected date range : {selected_start}  -  {selected_end}")
            
        tests = df_final["text"].unique()
        tests.sort()
        batteries = df_final["name_battery"].unique()
        batteries.sort()
        
        col1, col2= st.columns(2) 
        with col1:
            selected_tests = st.multiselect("Select specific tests", tests, key='text')
            if selected_tests is None: st.text("Empty")
        if selected_tests is None:
            selected_tests = []
        # else: st.text("filled")
        # df_final_tests = df_final.copy()
        df_final_tests = df_final.loc[df_final['text'].isin(selected_tests)]
        with col2:
            selected_batteries = st.multiselect("Select specific batteries", batteries, key='name_battery')
        if selected_batteries is None:
            selected_batteries = []
        df_final_batteries = df_final[df_final['name_battery'].isin(selected_batteries)]
        
        
    # # ************************************************************************************************************  
    # # all test of the selected players
    if option == 'Players Results':
        # df_final_players --> line 164
        # st.divider()
        st.subheader("Player Results ")
        
        if not df_final_players.empty:
            df_dict_test = split_df_by_test(df_final_players)
            for test, df in df_dict_test.items():
                
                # header - test and metrics
                df = df.sort_values(by='date')
                # get rid of all 0 values
                df = df.loc[df['test_result']!=0]
                
                # Calculate the mean value and the standard deviation
                mean_value = df['test_result'].mean()
                std_dev = df['test_result'].std()
                max_value = df['test_result'].max()
                min_value = df['test_result'].min()
                count_value = df['test_result'].count()
                
                st.divider()
                col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])
                with col1:
                    st.subheader(f"{test}")
                with col2:
                    st.metric(label="Mittelwert", value=round(mean_value,2), delta=f"{count_value} tests ")  
                with col3:
                    st.metric(label="Standardabweichung", value=round(std_dev,3))
                with col4:
                    st.metric(label="Maximum", value=round(max_value,3))
                with col5:
                    st.metric(label="Minimum", value=round(min_value,3))
                
                tab1, tab2, tab3 = st.tabs(["Tests Results", "Players Avg & Best", "Team Development"])
                with tab1:
                    col1, col2, col3 = st.columns([1.8,3,0.8])
                    with col1:
                        df = df.reindex(columns=['name','date','text','test_result','unit'])
                        df_short = df.reindex(columns=['name','date','test_result','unit'])
                        df_short = df_short.rename(columns={
                                    'name': 'Player',
                                    'date': 'Date',
                                    'test_result': 'Result',
                                    'unit': 'Unit'
                                })
                        st.dataframe(df_short, use_container_width=True, hide_index=True)
                    with col2:
                        fig = px.line(df, x='date', y='test_result', color='name', markers=True) 
                        # Customize x-axis tick format
                        fig.update_xaxes(tickformat="%d-%m-%y")
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")              
                        # Group the data by date and get the number of unique test data for each date
                        # grouped_df = df.groupby('date').first().reset_index()
                        # Add annotations to display the date for each marker on the x-axis
                        # for i in range(len(grouped_df)):
                        #     fig.add_annotation(x=grouped_df.date[i], y=grouped_df.test_result[i], text=grouped_df.date[i].strftime('%d-%m-%y'), showarrow=False)
                        
                        # fig.update_traces(textposition="bottom right")
                        st.plotly_chart(fig, theme=None, use_container_width=True)
                    with col3:
                        fig = px.box(df, y="test_result")
                        # Update box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:   
                        # df_best = df.groupby(['name', 'date'])['test_result'].max().reset_index()
                        df_best = df.groupby(['name'])['test_result'].max().reset_index()
                        df_best = df_best.sort_values(by='test_result', ascending=True)
                        fig = px.histogram(df_best, x='name', y='test_result', marginal = 'box', nbins=10, title='Best Test Result', labels={'name': '', 'test_result': 'Best Result'})
                        # Update bar and box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        # fig.update_layout(bargap=0.2)
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                    with col2:
                        # df_avg = df.groupby(['name', 'date'])['test_result'].mean().reset_index()
                        df_avg = df.groupby(['name'])['test_result'].mean().reset_index()
                        df_avg = df_avg.sort_values(by='test_result', ascending=True)
                        fig = px.histogram(df_avg, x='name', y='test_result', marginal = 'box', title='Average Test Result', labels={'name': ''})
                        fig.update_layout(bargap=0.2)
                        # Update bar color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                        # Update box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                with tab3:
                    df['date'] = pd.to_datetime(df['date'])
                    df['day'] = df['date'].dt.day
                    df['month'] = df['date'].dt.month
                    df['year'] = df['date'].dt.year
                    # Drop the 'day' column
                    df = df.drop('day', axis=1)
                    # Merge the 'month' and 'year' columns
                    df = df.assign(month_year=lambda x: x['year'].astype(str) + '-' + x['month'].astype(str))
                    # Rename the 'month_year' column
                    df = df.rename(columns={'month_year': 'year month'})
                        
                    fig_go = go.Figure()
                    fig_go.add_trace(go.Box(x=df['year month'], y=df['test_result'], name='results per month'))
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    # Update box color
                    fig_go.update_traces(marker_color='#b5b7ce')
                    st.plotly_chart(fig_go, theme="streamlit", use_container_width=True)  
                            
    # ************************************************************************************************************
    # Selected Tests    
    if option == 'Selected Tests':        
        if not df_final_tests is None:    
            # df_final_tests = df_final[df_final['text'].isin(selected_tests)]
            st.divider()
            st.subheader("Test Results ")
            
            if not df_final_players.empty:
                df_final_tests = df_final_tests[df_final_tests['name'].isin(selected_players)]
            df_final_tests = df_final_tests.reindex(columns=['name_battery', 'date', 'text', 'test_result', 'unit', 'comment', 'name', 'dob', 'gender', 'nationality', 'pos'])
            df_final_tests['text'] = df_final_tests['text'].replace(['"', "'"], "", regex=True)
            # df_final_tests['test_result'] = df_final_tests['test_result'].replace(',', ".", regex=True)
                
            df_dict_test = split_df_by_test(df_final_tests)
            for test, df in df_dict_test.items():
                
                # header - test and metrics
                df = df.sort_values(by='date')
                df = df.loc[df['test_result']!=0]
                # Calculate the mean value and the standard deviation
                mean_value = df['test_result'].mean()
                std_dev = df['test_result'].std()
                max_value = df['test_result'].max()
                min_value = df['test_result'].min()
                count_value = df['test_result'].count()
                
                st.divider()
                col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])
                with col1:
                    st.subheader(f"{test}")
                with col2:
                    st.metric(label="Mittelwert", value=round(mean_value,2), delta=f"{count_value} tests ")  
                with col3:
                    st.metric(label="Standardabweichung", value=round(std_dev,3))
                with col4:
                    st.metric(label="Maximum", value=round(max_value,3))
                with col5:
                    st.metric(label="Minimum", value=round(min_value,3))
                
                tab1, tab2, tab3 = st.tabs(["Tests Results", "Players Avg & Best", "Team Development"])
                with tab1:
                    col1, col2, col3 = st.columns([1.8,3,0.8])
                    with col1:
                        df = df.reindex(columns=['name','date','text','test_result','unit'])
                        df_short = df.reindex(columns=['name','date','test_result','unit'])
                        df_short = df_short.rename(columns={
                                    'name': 'Player',
                                    'date': 'Date',
                                    'test_result': 'Result',
                                    'unit': 'Unit'
                                })
                        st.dataframe(df_short, use_container_width=True, hide_index=True)
                    with col2:
                        fig = px.line(df, x='date', y='test_result', color='name', markers=True) 
                        # Customize x-axis tick format
                        fig.update_xaxes(tickformat="%d-%m-%y")
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        st.plotly_chart(fig, theme=None, use_container_width=True)
                    with col3:
                        fig = px.box(df, y="test_result")
                        # Update box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:   
                        # df_best = df.groupby(['name', 'date'])['test_result'].max().reset_index()
                        df_best = df.groupby(['name'])['test_result'].max().reset_index()
                        df_best = df_best.sort_values(by='test_result', ascending=True)
                        fig = px.histogram(df_best, x='name', y='test_result', marginal='box', nbins=10, title='Best Test Result', labels={'name': '', 'test_result': 'Best Result'})
                        # Update bar and box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        # fig.update_layout(bargap=0.2)
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                    with col2:
                        # df_avg = df.groupby(['name', 'date'])['test_result'].mean().reset_index()
                        df_avg = df.groupby(['name'])['test_result'].mean().reset_index()
                        df_avg = df_avg.sort_values(by='test_result', ascending=True)
                        fig = px.histogram(df_avg, x='name', y='test_result', marginal = 'box', title='Average Test Result', labels={'name': ''})
                        fig.update_layout(bargap=0.2)
                        # Update bar and box color
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                        fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        # Turn off x-axes and y-axes descriptions
                        fig.update_xaxes(title="")
                        fig.update_yaxes(title="")
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                with tab3:
                    df['date'] = pd.to_datetime(df['date'])
                    df['day'] = df['date'].dt.day
                    df['month'] = df['date'].dt.month
                    df['year'] = df['date'].dt.year
                    # Drop the 'day' column
                    df = df.drop('day', axis=1)
                    # Merge the 'month' and 'year' columns
                    df = df.assign(month_year=lambda x: x['year'].astype(str) + '-' + x['month'].astype(str))
                    # Rename the 'month_year' column
                    df = df.rename(columns={'month_year': 'year month'})
                        
                    fig_go = go.Figure()
                    fig_go.add_trace(go.Box(x=df['year month'], y=df['test_result'], name='results per month'))
                    # Update box color
                    fig_go.update_traces(marker_color='#b5b7ce')
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    st.plotly_chart(fig_go, theme="streamlit", use_container_width=True)  
                
    # ************************************************************************************************************
    # Selected Batteries   
    if option == 'Selected Batteries':
        # # ************************************************************************************************************
        df_final_batteries = df_final[df_final['name_battery'].isin(selected_batteries)]
        st.subheader("Batteries Results")
        # if not df_final_batteries.empty:
        if not df_final_players.empty:
            df_final_batteries = df_final_batteries[df_final_batteries['name'].isin(selected_players)]
            
        df_dict_test = split_df_by_test(df_final_batteries)
        for test, df in df_dict_test.items():
            
            # header - test and metrics
            df = df.sort_values(by='date')
            df = df.loc[df['test_result']!=0]
            # Calculate the mean value and the standard deviation
            mean_value = df['test_result'].mean()
            std_dev = df['test_result'].std()
            max_value = df['test_result'].max()
            min_value = df['test_result'].min()
            count_value = df['test_result'].count()
            
            st.divider()
            col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])
            with col1:
                st.subheader(f"{test}")
            with col2:
                st.metric(label="Mittelwert", value=round(mean_value,2), delta=f"{count_value} tests ")  
            with col3:
                st.metric(label="Standardabweichung", value=round(std_dev,3))
            with col4:
                st.metric(label="Maximum", value=round(max_value,3))
            with col5:
                st.metric(label="Minimum", value=round(min_value,3))
            
            tab1, tab2, tab3 = st.tabs(["Tests Results", "Players Avg & Best", "Team Development"])
            with tab1:
                col1, col2, col3 = st.columns([1.8,3,0.8])
                with col1:
                    df = df.reindex(columns=['name','date','text','test_result','unit'])
                    df_short = df.reindex(columns=['name','date','test_result','unit'])
                    df_short = df_short.rename(columns={
                                'name': 'Player',
                                'date': 'Date',
                                'test_result': 'Result',
                                'unit': 'Unit'
                            })
                    st.dataframe(df_short, use_container_width=True, hide_index=True)
                with col2:
                    fig = px.line(df, x='date', y='test_result', color='name', markers=True) 
                    # Customize x-axis tick format
                    fig.update_xaxes(tickformat="%d-%m-%y")
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    st.plotly_chart(fig, theme=None, use_container_width=True)
                with col3:
                    fig = px.box(df, y="test_result")
                    # Update box color
                    fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    
            with tab2:
                col1, col2 = st.columns(2)
                with col1:   
                    # df_best = df.groupby(['name', 'date'])['test_result'].max().reset_index()
                    df_best = df.groupby(['name'])['test_result'].max().reset_index()
                    df_best = df_best.sort_values(by='test_result', ascending=True)
                    fig = px.histogram(df_best, x='name', y='test_result', marginal='box', nbins=10, title='Best Test Result')
                    # Update bar and box color
                    fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                    fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    # fig = px.histogram(df_best, x='name', y='test_result', marginal = 'box', nbins=10, title='Best Test Result', labels={'name': '', 'test_result': 'Best Result'})
                    # fig.update_layout(bargap=0.2)
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    
                with col2:
                    # df_avg = df.groupby(['name', 'date'])['test_result'].mean().reset_index()
                    df_avg = df.groupby(['name'])['test_result'].mean().reset_index()
                    df_avg = df_avg.sort_values(by='test_result', ascending=True)
                    fig = px.histogram(df_avg, x='name', y='test_result', marginal='box', title='Average Test Result')
                    # Update bar and box color
                    fig.update_traces(marker_color='#b5b7ce', selector=dict(type='histogram'))
                    fig.update_traces(marker_color='#b5b7ce', selector=dict(type='box'))
                    # Turn off x-axes and y-axes descriptions
                    fig.update_xaxes(title="")
                    fig.update_yaxes(title="")
                    # fig = px.histogram(df_avg, x='name', y='test_result', marginal = 'box', title='Average Test Result', labels={'name': ''})
                    fig.update_layout(bargap=0.2)
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    
            with tab3:
                df['date'] = pd.to_datetime(df['date'])
                df['day'] = df['date'].dt.day
                df['month'] = df['date'].dt.month
                df['year'] = df['date'].dt.year
                # Drop the 'day' column
                df = df.drop('day', axis=1)
                # Merge the 'month' and 'year' columns
                df = df.assign(month_year=lambda x: x['year'].astype(str) + '-' + x['month'].astype(str))
                # Rename the 'month_year' column
                df = df.rename(columns={'month_year': 'year month'})
                    
                fig_go = go.Figure()
                fig_go.add_trace(go.Box(x=df['year month'], y=df['test_result'], name='results per month'))
                # Update box color
                fig_go.update_traces(marker_color='#b5b7ce')
                # Turn off x-axes and y-axes descriptions
                fig.update_xaxes(title="")
                fig.update_yaxes(title="")
                st.plotly_chart(fig_go, theme="streamlit", use_container_width=True)  
                        
    # # ************************************************************************************************************
    # General infos and graphs - when how many of which test
    if option == 'General':
        st.subheader(f"Generel Information: Tests from {selected_start} to {selected_end}")
        df_batteries_date = df_final.groupby(['name_battery', 'date']).size().reset_index(name='# of tests')
        df_batteries_date = df_batteries_date.sort_values(by='date')
        # initial graphs of all tests
            
        # # ****
        # # Metrics - Header
        # # ****
        fig = px.line(df_batteries_date, x='date', y='# of tests', title="Amount of tests ", color='name_battery')
        fig_pie = px.pie(df_batteries_date, values='# of tests', names='name_battery')
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col5.metric(label="Total tests:", value=df_final['id_battery'].count())  
        col6.metric(label="Avg. tests/day", value=round(df_final.groupby('date')['id_battery'].count().mean()), delta=round(df_final.groupby('date')['id_battery'].count().max())) 
        # col3.metric(label="Number of batteries", value=round(df_final.groupby(['name_battery', 'date']).count())) 
        # col4.metric(label="Average Mails / Month", value=round(df_mail_month['Total Mails'].mean()))

        fig_2 = px.bar(df_batteries_date, x="date", y="# of tests", text_auto='.3s', title="Amount of tests ", color='name_battery')
        # fig_2.update_traces(marker_color='orange')
        # fig_2.update_layout(bargap=0.8)
        # fig_2.update_layout(width=700, height=445, bargap=0.3)
        fig_2.update_xaxes(
                rangeslider_visible=False,
                rangeselector=dict(
                    buttons=list([
                        dict(step="all"),
                        dict(count=3, label="last 3 month", step="month", stepmode="backward"),
                        dict(count=6, label="last 6 month", step="month", stepmode="backward"),
                        dict(count=1, label="This year", step="year", stepmode="todate"),
                        dict(count=1, label="1y back", step="year", stepmode="backward"),
                        dict(count=2, label="2y back", step="year", stepmode="backward")
                    ])
                )
            )
        st.plotly_chart(fig_2, theme="streamlit", use_container_width=True)
        # st.plotly_chart(fig, use_container_width=True)
        
        col_1, col_2 = st.columns([2,3])
        with col_1:
            st.dataframe(df_batteries_date, use_container_width=True, hide_index=True)

        with col_2:
            st.plotly_chart(fig_pie, theme="streamlit", use_container_width=True)
         
    # # ************************************************************************************************************
    #  CSV Exports
    
    @st.cache_data
    def convert_df(df):
        return df.to_csv().encode('utf-8')

    if option == 'CSV Export':
        st.header("CSV Exports")
        st.subheader("Player Results")
        
        if not df_final_players.empty:
            with st.expander("Export Player Results (all tests done by the selected players)", expanded=True):  
                st.subheader(f"All results of the selected players from {selected_start} to {selected_end}")
                
                df_final_players = clean_df(df_final_players)
                # df_long_players = pd.pivot_table(df_final_players, values=['test_result'], index=['name'], columns=['text','period'], 
                df_long_players = pd.pivot_table(df_final_players, values=['test_result'], index=['name'], columns=['text','year month'], 
                                                aggfunc={'test_result': max})
                df_long_players = df_long_players.reset_index()
                st.dataframe(df_long_players, use_container_width=True, hide_index=True)
                
                csv = convert_df(df_long_players)
                st.download_button(
                    "CSV Export",
                    csv,
                    "player_tests_wide.csv",
                    "text/csv",
                    # key='browser-data'
                )
                
                st.dataframe(df_final_players, use_container_width=True, hide_index=True)
                csv = convert_df(df_final_players)
                st.download_button(
                    "CSV Export",
                    csv,
                    "player_tests_long.csv",
                    "text/csv",
                )
        else:
            st.text("Please select at least one player") 
        
        st.divider()                  
        st.subheader("Selected Tests")
        if not df_final_tests.empty:
            
            if not df_final_players.empty:
                df_final_tests = df_final_tests[df_final_tests['name'].isin(selected_players)]
            df_final_tests = clean_df(df_final_tests)

            with st.expander("Export Selected Test Results", expanded=True):  
                # ****
                st.subheader(f"Test results of the selected tests fom {selected_start} to {selected_end}")
                df_long_tests = pd.pivot_table(df_final_tests, values=['test_result'], index=['name'], columns=['text','year month'], 
                                                aggfunc={'test_result': max})
                df_long_tests = df_long_tests.reset_index()
                st.dataframe(df_long_tests, use_container_width=True, hide_index=True)
                
                csv = convert_df(df_long_tests)
                st.download_button(
                    "CSV Export",
                    csv,
                    "tests_wide.csv",
                    "text/csv",
                    # key='browser-data'
                )
                        
                st.divider()
                
                st.dataframe(df_final_tests, use_container_width=True, hide_index=True)
                
                csv = convert_df(df_final_tests)
                st.download_button(
                    "CSV Export",
                    csv,
                    "tests_long.csv",
                    "text/csv",
                    # key='browser-data'
                )
        else:
            st.text("Please select at least one test and one player")  
             
        st.divider()                            
        st.subheader("Selected Batteries")                    
        if not df_final_batteries.empty: 
            if not df_final_players.empty:
                df_final_batteries = df_final_batteries[df_final_batteries['name'].isin(selected_players)]
            df_final_batteries = clean_df(df_final_batteries)
            
            with st.expander("Export Selected Batteries", expanded=True):
                
                df_long_batteries = pd.pivot_table(df_final_batteries, values=['test_result'], index=['name'], columns=['text','year month'], 
                                                aggfunc={'test_result': max})
                df_long_batteries = df_long_batteries.reset_index()
                st.dataframe(df_long_batteries, use_container_width=True, hide_index=True)
                
                csv = convert_df(df_long_batteries)
                st.download_button(
                    "CSV Export",
                    csv,
                    "batteries_wide.csv",
                    "text/csv",
                    # key='browser-data'
                )
                # ****
                st.divider()
                df_final_batteries = df_final_batteries.reindex(columns=['name_battery','name','date','text','test_result','unit','comment','gender','dob','pos','nationality'])
                # fig = px.line(df_final_batteries, x='date', y='test_result', title=f"Test results {test}", color='name', markers=True) 
                # st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                st.dataframe(df_final_batteries, use_container_width=True, hide_index=True)
                
                csv = convert_df(df_final_batteries)
                st.download_button(
                    "CSV Export",
                    csv,
                    "batteries.csv",
                    "text/csv",
                    # key='browser-data'
                )
        else:
            st.text("Please select at least one battery")                 
                
        # # ************************************************************************************************************
        # All Tests of all selected players - grouped by player
        st.divider()                  
        st.subheader("All Tests of all Players")
        with st.expander(f"All tests and results of players from {selected_start} to {selected_end}", expanded=False):  
            st.subheader("All results and information ")
            df_final = df_final.reindex(columns=['name_battery', 'date', 'text', 'description', 'test_result', 'unit', 'comment', 'name', 'dob', 'gender', 'nationality', 'pos'])
            
            # get rid of all 0 values
            
            df_final = df_final.loc[df_final['test_result']!=0]
            df_final['text'] = df_final['text'].replace(['"', "'"], "", regex=True)
            
            df_final['date'] = pd.to_datetime(df_final['date'])
            df_final['day'] = df_final['date'].dt.day
            df_final['month'] = df_final['date'].dt.month
            df_final['year'] = df_final['date'].dt.year
            df_final = df_final.drop('day', axis=1)
            df_final = df_final.assign(month_year=lambda x: x['year'].astype(str) + '-' + x['month'].astype(str))
            df_final = df_final.rename(columns={'month_year': 'year month'})
            
            st.dataframe(df_final, use_container_width=True, hide_index=True) 
            
            col1, col2 = st.columns([3,1])
            with col1:
                df_long = pd.pivot_table(df_final, values=['test_result'], index=['name'], columns=['text','year month'], 
                                            aggfunc={'test_result': max})
                df_long = df_long.reset_index()
                st.dataframe(df_long, use_container_width=True, hide_index=True)
                
            with col2:
                df_final = df_final.reindex(columns=['name','date','text','test_result','unit'])
                df_short = df_final.reindex(columns=['name','date','test_result','unit'])
                st.dataframe(df_short, use_container_width=True, hide_index=True)
                
        # # ************************************************************************************************************
        
        # if not df_final_players.empty:
        #     with st.expander("Player - All results grouped by player", expanded=False):
                        
        #         st.markdown('------')
        #         st.subheader("All results grouped by player")
        #         df_dict = split_df_by_player(df_final_players)
        #         for name, df in df_dict.items():
        #             st.divider()
        #             st.subheader(name)
        #             st.dataframe(df, use_container_width=True, hide_index=True)

        #             df_long = pd.pivot_table(df, values=['test_result'], index=['name'], columns=['date','text'], aggfunc={'test_result': max})
        #             df_long = df_long.reset_index()
        #             st.dataframe(df_long, use_container_width=True, hide_index=True)
                            
        # # ************************************************************************************************************
        
                
