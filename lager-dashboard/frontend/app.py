import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Reservedels Dashboard", layout="wide")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/upload_csv/")

st.title("Reservedels Dashboard")
st.write("Upload forbrugsdata for reservedele")

st.markdown("---")


uploaded_file = st.file_uploader("Vælg en csv fil", type="csv")
if uploaded_file is not None:
    st.subheader("Data preview")

    try:
        df_preview = pd.read_csv(uploaded_file)
        st.dataframe(df_preview)
    except Exception as e:
        st.error("kunne ikke læse filen: ", str(e))

    st.markdown("---")

    if st.button("Analysér data", type="primary"):
        with st.spinner("Sender data til backend"):
            # Streamlit læser filen fra byte 0
            uploaded_file.seek(0)

            # Klargør payload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}

            try:
                response = requests.post(API_URL, files=files)

                if response.status_code == 200:
                    st.success("Filen blev analyseret")

                    result = response.json()
                    summary = result.get("data_summary", {})
                    analyse_data = result.get("analyse_resultat", [])

                    st.subheader("Fil-information")
                    col1, col2 = st.columns(2)
                    col1.metric("Antal rækker", summary.get("antal_rækker", 0))
                    col2.metric("Antal kolonner", len(summary.get("kolonner", [])))

                    st.markdown("---")

                    st.subheader("Beregnet Lageranalyse")
                    st.write(
                        "Her ses det totale forbrug og udskiftningsfrekvensen per reservedel."
                    )

                    if analyse_data:
                        # Konverterer JSON-listen tilbage til en DataFrame
                        df_analyse = pd.DataFrame(analyse_data)

                        # Formatér kolonner i streamlit
                        st.dataframe(
                            df_analyse,
                            use_container_width=True,
                            hide_index=True,  # Skjuler det unødvendige række-nummer (0, 1, 2...)
                        )
                    else:
                        st.info("Ingen gyldig data kunne udtrækkes.")

                    st.markdown("---")
                    st.subheader("Visuelle grafer")

                    # Opret to kolonner for at vise graferne pænt ved siden af hinanden
                    fig_col1, fig_col2 = st.columns(2)

                    with fig_col1:
                        st.write("**Top 4: Mest købte produkter**")
                        # Sorter så de mest brugte er i toppen
                        df_forbrug = df_analyse.sort_values(
                            "total_usage", ascending=True
                        ).tail(10)

                        # Opret Matplotlib figur
                        fig1, ax1 = plt.subplots(figsize=(6, 4))
                        ax1.barh(
                            df_forbrug["product_id"],
                            df_forbrug["total_usage"],
                            color="#4B8BBE",
                        )
                        ax1.set_xlabel("Totalt antal brugt")
                        ax1.set_title("Forbrugsvolumen")

                        # Tegn figuren i Streamlit
                        st.pyplot(fig1)

                    # AI Response
                    st.markdown("---")

                    ai_data = result.get("ai_response", {})

                    st.subheader("AI-Assistentens Analyse")

                    if ai_data.get("status") == "success":
                        # Vis Mistrals svar i en fremhævet boks
                        st.info(ai_data.get("text"))
                    else:
                        # Hvis der f.eks. mangler en API-nøgle
                        st.warning(
                            f"AI-analysen kunne ikke gennemføres: {ai_data.get('message')}"
                        )

                else:
                    st.error(
                        f"Fejl fra backend: {response.json().get('detail', response.text)}"
                    )
            except requests.exceptions.ConnectionError:
                st.error(
                    f"Fejl fra backend, vær sikker på at du kører på den rigtige port: {response.status_code}): {response.text}"
                )
