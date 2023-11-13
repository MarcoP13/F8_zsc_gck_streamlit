from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import streamlit as st

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials, project=credentials.project_id,)


@st.cache_data
def load_season():
    rows = client.query('Select id, name from panoply.mysql_tb_seasons WHERE id>4').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_season', 'name': 'season'}, inplace=True)
    return df

@st.cache_data
# all informations about the players: name, dob, nationality etc
def fetch_players():
    rows = client.query('Select id, fname, lname, birth_date, nationality, position, gender from panoply.mysql_tb_player').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_player'}, inplace=True)
    df['name'] = df['lname'] + ' ' + df['fname']
    df.drop(['lname', 'fname'], axis=1, inplace=True)
    df.rename(columns={'birth_date': 'dob'}, inplace=True)
    return df
    
@st.cache_data
#  all batteries of the choosen club
def fetch_batteries_template():
    rows = client.query('Select id, id_season, id_agegroup, name, description, created, id_user from panoply.mysql_tb_dossier_clubtests WHERE id_club=5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_battery',
                   'id_season': 'id_season_battery',
                   'id_agegroup': 'id_agegroup_battery',
                   'name': 'name_battery',
                   'description': 'description_battery',
                   'created': 'created_battery'}, inplace=True)
    return df

@st.cache_data
# all players of each batterie 
def fetch_batteries_players():
    rows = client.query('Select id, id_user, id_player, id_season, id_agegroup, id_clubtest, date, observer, description from panoply.mysql_tb_dossier_clubtests_results WHERE id_club=5').result()
    # rows = client.query('Select id, id_user, id_player, id_season, id_agegroup, id_clubtest, created, date, observer, description from panoply.mysql_tb_dossier_clubtests_results WHERE id_club=5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_test_battery',
                   'id_clubtest': 'id_battery'}, inplace=True)
    # df.drop(['__databasename', '__senttime', '__panoply_id', '__panoply_pk','__state'], axis=1, inplace=True)
    # df.query('id_club == 5', inplace=True)
    return df

@st.cache_data
def fetch_testsexercises():
    rows = client.query('Select * from panoply.mysql_tb_dossier_clubtests_testexercises').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.drop(['id','ord','__databasename', '__senttime', '__panoply_id', '__panoply_pk','__state','__tablename', '__updatetime'], axis=1, inplace=True)
    df.rename(columns={'id_clubtest': 'id_battery'}, inplace=True)
    return df
    
@st.cache_data
# name, description and unit of the single test
def fetch_exercise_info():
    rows = client.query('Select id, text, description, unit from panoply.mysql_tb_test_exercises WHERE id_club = 5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_testexercise'}, inplace=True)
    return df

@st.cache_data
def fetch_testsexercises_results():
    rows = client.query('Select id_user, id_player, id_season, id_agegroup, id_clubtest_result, id_clubtest, id_testexercise, valuation, comment from panoply.mysql_tb_dossier_clubtests_testexercises_results WHERE id_club=5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id_agegroup': 'id_agegroup_test', 'id_clubtest': 'id_battery', 'valuation':'test_result'}, inplace=True)
    # df = pd.DataFrame(rows_list, columns=['id_user','id_player','id_season', 'id_agegroup_test', 'id_clubtest_result', 'id_battery', 'id_testexercise', 'test_result', 'comment'])
    return df
 
@st.cache_data
# all teams of a specific club
def fetch_agegroup():
    rows = client.query('Select id, name from panoply.mysql_tb_agegroup').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_agegroup'}, inplace=True)
    return df

@st.cache_data
def fetch_club_agegroup():
    rows = client.query('SELECT id_season, id_agegroup FROM panoply.mysql_tb_club_season_agegroup_skill_level WHERE id_club=5 AND id_season>=5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'id': 'id_agegroup'}, inplace=True)
    return df
   
@st.cache_data
# all teams of a specific club
def fetch_teams():
    rows = client.query('Select id, id_season, id_agegroup, name from panoply.mysql_tb_team_season_club_agegroup_skill_level WHERE id_club = 5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    df.rename(columns={'name': 'team_name'}, inplace=True)
    return df

@st.cache_data
# all players filtered by id_club -> all players of an id_team
def fetch_team_players():
    rows = client.query('Select id_player, id_team, id_season from panoply.mysql_tb_player_season_club_agegroup_skill_level_team WHERE id_club = 5').result()
    rows_list = [dict(row) for row in rows]
    df = pd.DataFrame(rows_list)
    return df