#requirements
import pandas as pd
import streamlit as st
import random
import st_aggrid as AgGrid
import re
from statistics import mode
import sqlalchemy as db
import time

st.set_page_config(page_title="Movies", page_icon=":camera:", layout="wide",initial_sidebar_state="expanded")

#function to load user submission data
#@st.cache(ttl=60, hash_funcs=True, suppress_st_warning=True, allow_output_mutation=True)
#def get_codes():
user = st.secrets["postgres"]["user"]
password = st.secrets["postgres"]["password"]
host = st.secrets["postgres"]["host"]
database = st.secrets["postgres"]["database"]
conn_str = f"postgresql://{user}:{password}@{host}/{database}"
engine = db.create_engine(conn_str)
connection = db.engine.connect()
metadata = db.MetaData()
user_codes_pg = db.Table('user_codes', metadata, autoload=True, autoload_with=engine)
user_codes = select([user_codes_pg]) 
ResultProxy = connection.execute(user_codes)
ResultSet = ResultProxy.fetchall()
user_codes_table = pd.DataFrame(ResultSet, columns=["code", "email"])
#    return user_codes_table
#codes = get_codes()
#codes

#function to load code data
#@st.cache(ttl=60, hash_funcs=True, suppress_st_warning=True, allow_output_mutation=True)
#def get_submissions():
user = st.secrets["postgres"]["user"]
password = st.secrets["postgres"]["password"]
host = st.secrets["postgres"]["host"]
database = st.secrets["postgres"]["database"]
conn_str = f"postgresql://{user}:{password}@{host}/{database}"
engine = create_engine(conn_str)
connection = engine.connect()
metadata = MetaData()
user_submits_pg = Table('user_submissions', metadata, autoload=True, autoload_with=engine)

user_submits = select([user_submits_pg]) 
ResultProxy = connection.execute(user_submits)
ResultSet = ResultProxy.fetchall()
user_submits_table = pd.DataFrame(ResultSet, columns=["code", "email", "color","language","genre","score", "id"])
#    return user_submits_table
#submissions = get_submissions()
#submissions

#function to load movie repo data
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def load_data():
    dataset = pd.read_csv("https://raw.githubusercontent.com/maxwellknowles/movies/main/movie_metadata.csv")
    dataset = dataset[["color","director_name","duration","gross","genres","movie_title","plot_keywords","movie_imdb_link","language","country","content_rating","budget","title_year","imdb_score"]]
    for i in range(0,len(dataset)):
        dataset['title_year'][i] = float(dataset['title_year'][i])
        return dataset

#grab movie repo data
dataset = load_data()

#function to generate code
@st.cache()
def get_code():
    code = random.randint(1111,9999)
    return code

genres = []
for i in range(0,len(dataset)):
    split = dataset["genres"][i].split("|")
    genres += split
genres = set(genres)

st.header("The Ultimate Group Movie-Choosing Algorithm")
st.subheader("The Repository")
AgGrid(dataset)
st.caption("Your group's responses will allow the app to narrow the data")
st.subheader("Let's do this...")
action = st.selectbox("Do you want to start a group movie-choosing experience or participate in one?", ("Initiate", "Join"))

if action == "Initiate":

    codes = user_codes_table

    if st.checkbox("Generate code"):
        email = st.text_input("Please enter your email")
        code = get_code()
        st.write("Tell your friends to visit this website and enter this code: "+str(code))
        if st.button("Create new record"):
            #Inserting new record
            query = insert(user_codes_pg).values(user_code=code, user_email=email) 
            ResultProxy = connection.execute(query)

        if code:
            color = st.selectbox("filter by color",list(dataset.color.unique()))
            language = st.selectbox("filter by language",list(dataset.language.unique()))
            genre = st.multiselect("select genres",genres)
            score = st.slider("select minimum score of movie",min_value=0.0,max_value=10.0,step=0.2)

            if st.button("Submit"):
                #Inserting new record
                query = insert(user_submits_pg).values(user_code=code, user_email=email, color=color, language=language, genre=genre, score=score) 
                ResultProxy = connection.execute(query)
                st.success("Nice!")

                user_submits_pg = Table('user_submissions', metadata, autoload=True, autoload_with=engine)
                user_submits = select([user_submits_pg]) 
                ResultProxy = connection.execute(user_submits)
                ResultSet = ResultProxy.fetchall()
                user_submits_table = pd.DataFrame(ResultSet, columns=["code","email","color","language","genre","score","id"])
                movies = user_submits_table
                movies = movies[(movies["code"]==code)]
                st.write("We've received "+str(len(movies))+" submissions for your group so far.")

                color = movies["color"].mode()[0]
                language = movies["language"].mode()[0]
                genre = []
                for i in range(len(movies)):
                    string = re.sub(r"[[\]]",'',movies["genre"][i])
                    split = string.split(",")
                    genre += split
                genre = mode(genre)
                genre = genre.strip("\'")
                score = movies["score"].mean()

                st.write("Starting with "+str(len(dataset))+" movies...")
                for i in range(0,len(dataset)):
                    if genre not in dataset["genres"][i]:
                        dataset = dataset.drop(labels=i, axis=0)
                    else:
                        pass
                st.write("Genre preferences filtered down to "+str(len(dataset))+"...")
                dataset = dataset.reset_index(drop=True)

                if len(dataset) > 5:
                    dataset = dataset[(dataset["color"]==color)]
                else:
                    pass
                if len(dataset) > 5:
                    dataset = dataset[(dataset["language"]==language)]
                else:
                    pass
                if len(dataset) > 5:
                    dataset = dataset[(dataset["imdb_score"]>=score)]
                else:
                    pass
                dataset = dataset.reset_index(drop=True)
                st.write("Other preferences resulting in "+str(len(dataset))+" option(s)...")
                
                st.write("Here's your group's set of recommendations!")
                for i in range(len(dataset)):
                    st.caption(dataset["movie_title"][i])
                AgGrid(dataset)

        else: 
            pass

else:
    code_entry = st.text_input("Please enter the code for your group...","0000")
    email = st.text_input("Please enter your email")
    user_codes_pg = Table('user_codes', metadata, autoload=True, autoload_with=engine)
    user_codes = select([user_codes_pg]) 
    ResultProxy = connection.execute(user_codes)
    ResultSet = ResultProxy.fetchall()
    user_codes_table = pd.DataFrame(ResultSet, columns=["code", "email"])
    codes = user_codes_table
    
    if code_entry:
        if code_entry in list(codes["code"]):
            color = st.selectbox("filter by color",list(dataset.color.unique()))
            language = st.selectbox("filter by language",list(dataset.language.unique()))
            genre = st.multiselect("select genres",genres)
            score = st.slider("select minimum score of movie",min_value=0.0,max_value=10.0,step=0.2)

            if st.button("Submit"):
                #Inserting new record
                query = insert(user_submits_pg).values(user_code=code_entry, user_email=email, color=color, language=language, genre=genre, score=score,id=code_entry+"-"+email) 
                ResultProxy = connection.execute(query)
                st.success("Nice!")

                user_submits_pg = Table('user_submissions', metadata, autoload=True, autoload_with=engine)
                user_submits = select([user_submits_pg]) 
                ResultProxy = connection.execute(user_submits)
                ResultSet = ResultProxy.fetchall()
                user_submits_table = pd.DataFrame(ResultSet, columns=["code","email","color","language","genre","score","id"])
                movies = user_submits_table
                movies = movies[(movies["code"]==code_entry)]
                st.write("We've received "+str(len(movies))+" submissions for your group so far.")

                color = movies["color"].mode()[0]
                language = movies["language"].mode()[0]
                genre = []
                for i in range(len(movies)):
                    genre += movies["genre"][i]
                genre = mode(genre)
                genre = genre.strip("\'")
                score = movies["score"].mean()
                st.write("Starting with "+str(len(dataset))+" movies...")
                for i in range(0,len(dataset)):
                    if genre not in dataset["genres"][i]:
                        dataset = dataset.drop(labels=i, axis=0)
                    else:
                        pass
                with st.spinner('Filtering by genre...'):
                    time.sleep(3)    
                st.write("Genre preferences filtered down to "+str(len(dataset))+"...")
                dataset = dataset.reset_index(drop=True)

                if len(dataset) > 5:
                    dataset = dataset[(dataset["color"]==color)]
                else:
                    pass
                with st.spinner('Filtering by color...'):
                    time.sleep(1)
                if len(dataset) > 5:
                    dataset = dataset[(dataset["language"]==language)]
                else:
                    pass
                with st.spinner('Filtering by language...'):
                    time.sleep(1)
                if len(dataset) > 5:
                    dataset = dataset[(dataset["imdb_score"]>=score)]
                else:
                    pass
                dataset = dataset.reset_index(drop=True)
                with st.spinner('Filtering by IMDB score...'):
                    time.sleep(1)
                st.write("Preferences resulting in "+str(len(dataset))+" option(s)...")
                
                st.write("Here's your group's set of recommendations!")
                for i in range(len(dataset)):
                    st.caption(dataset["movie_title"][i])
                AgGrid(dataset)

        else:
            st.write("Looks like that code doesn't exist :(")

        
