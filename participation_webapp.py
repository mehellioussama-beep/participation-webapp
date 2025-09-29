#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import random
import datetime
import os

DATAFILE = "participation_data.xlsx"

def init_data():
    if not os.path.exists(DATAFILE):
        female_names = [f"F_Student_{i+1}" for i in range(13)]
        male_names = [f"M_Student_{i+1}" for i in range(15)]
        students = []
        idx = 1
        for name in female_names:
            students.append({"ID": idx, "Name": name, "Gender": "F", "Score": 0})
            idx += 1
        for name in male_names:
            students.append({"ID": idx, "Name": name, "Gender": "M", "Score": 0})
            idx += 1
        df = pd.DataFrame(students)
        history = pd.DataFrame(columns=["Timestamp", "Activity", "Type", "Target", "Delta", "NewScore", "Notes"])
        with pd.ExcelWriter(DATAFILE, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, index=False, sheet_name="Students")
            history.to_excel(writer, index=False, sheet_name="History")
    else:
        df = pd.read_excel(DATAFILE, sheet_name="Students")
        history = pd.read_excel(DATAFILE, sheet_name="History")
    return df, history

def save_data(df, history):
    with pd.ExcelWriter(DATAFILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
        history.to_excel(writer, index=False, sheet_name="History")

st.set_page_config(page_title="Participation Manager", layout="wide")
st.title("📊 Class Participation Manager")

df, history = init_data()

st.sidebar.header("Options")
action = st.sidebar.radio("Choose action", ["View Students", "Generate Groups", "Random Pick", "Give Points", "History", "Manage Students"])

if action == "View Students":
    st.subheader("Student List")
    st.dataframe(df.style.applymap(lambda v: "color: green;" if isinstance(v,int) and v>0 else ("color: red;" if isinstance(v,int) and v<0 else "")))

elif action == "Generate Groups":
    st.subheader("Random Mixed Groups")
    group_size = st.number_input("Group size", min_value=2, max_value=10, value=4, step=1)
    males = df[df["Gender"].str.upper()=="M"].sample(frac=1).to_dict('records')
    females = df[df["Gender"].str.upper()=="F"].sample(frac=1).to_dict('records')
    combined = []
    while males or females:
        if males: combined.append(males.pop(0))
        if females: combined.append(females.pop(0))
    groups = [combined[i:i+group_size] for i in range(0, len(combined), group_size)]
    for i, g in enumerate(groups, 1):
        st.write(f"**Group {i}:** " + ", ".join([f"{p['Name']} ({p['Gender']})" for p in g]))

elif action == "Random Pick":
    st.subheader("Random Student Picker")
    if st.button("Pick Student 🎲"):
        r = df.sample(1).iloc[0]
        st.success(f"🎉 {r['Name']} ({r['Gender']}) - Current Score: {r['Score']}")

elif action == "Give Points":
    st.subheader("Give or Subtract Points")
    student_choices = st.multiselect("Select students", df["Name"].tolist())
    delta = st.number_input("Points (+ or -)", value=1, step=1)
    note = st.text_input("Optional note")
    if st.button("Apply Points"):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for name in student_choices:
            idx = df[df["Name"]==name].index[0]
            df.at[idx, "Score"] += delta
            newscore = df.at[idx, "Score"]
            history = pd.concat([history, pd.DataFrame([{
                "Timestamp": ts,
                "Activity": "Manual",
                "Type": "Individual",
                "Target": name,
                "Delta": delta,
                "NewScore": newscore,
                "Notes": note
            }])], ignore_index=True)
        save_data(df, history)
        st.success("Points updated!")

elif action == "History":
    st.subheader("History of Activities")
    st.dataframe(history)

elif action == "Manage Students":
    st.subheader("Manage Students")
    new_name = st.text_input("New student name")
    new_gender = st.radio("Gender", ["M","F"])
    if st.button("Add Student"):
        new_id = int(df["ID"].max())+1 if len(df)>0 else 1
        df = pd.concat([df, pd.DataFrame([{"ID":new_id,"Name":new_name,"Gender":new_gender,"Score":0}])], ignore_index=True)
        save_data(df, history)
        st.success(f"Added {new_name} ({new_gender}).")
    remove_name = st.selectbox("Remove student", [""]+df["Name"].tolist())
    if st.button("Remove"):
        df = df[df["Name"]!=remove_name]
        save_data(df, history)
        st.warning(f"Removed {remove_name}.")
    if st.button("Reset all scores"):
        df["Score"]=0
        history = history.iloc[0:0]
        save_data(df, history)
        st.error("All scores reset!")
