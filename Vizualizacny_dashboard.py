import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from bokeh.plotting import figure
from bokeh.models import HoverTool
import altair as alt
import io

# konfiguracia stranky
st.set_page_config(page_title="Vizualizačný Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stFileUploader"] div:first-child {
    font-size: 24px !important;
}
    </style>
    """, unsafe_allow_html=True)

st.header(":violet[Interaktívny Vizualizačný Dashboard]")

subor = st.file_uploader(" Nahrajte dataset (CSV, Excel)",type=['csv', 'xlsx', 'xls'], help="Podporované formáty: CSV, Excel")

if subor is not None:
    # nacitanie suboru
    try:
        if subor.name.endswith('.csv'):
            df = pd.read_csv(subor, sep=None, engine='python') # dokaze spracovat aj nespravne naformatovane csv
        else:
            df = pd.read_excel(subor)

        stl1, stl2, stl3, stl4 = st.columns(4)
        with stl1:
            st.metric("Počet riadkov", df.shape[0])
        with stl2:
            st.metric("Počet stĺpcov", df.shape[1])
        with stl3:
            st.metric("Numerické stĺpce", len(df.select_dtypes(include=['number']).columns))
        with stl4:
            st.metric("Kategoriálne stĺpce", len(df.select_dtypes(include=['object']).columns))
        # zobrazenie hlavicky datasetu
        with st.expander("Zobraziť dataset"):
             st.write(df.head(10))

        # ziskanie stlpcov
        numericke= df.select_dtypes(include=['number']).columns.tolist()
        kategorialne = df.select_dtypes(include=['object']).columns.tolist()
        sltpce = df.columns.tolist()

        # vyber rezimu
        mode = st.radio(
            " Vyberte režim vizualizácie:",
            ["Štandardný režim", "Porovnávací režim"],
            horizontal=True
        )
        if mode == "Štandardný režim":
            stl1, stl2 = st.columns(2)
    
        with stl1:
            kniznica = st.selectbox(
                " Vyberte vizualizačnú knižnicu:",
                ["Matplotlib", "Seaborn", "Plotly", "Bokeh", "Altair"]
            )
    
        with stl2:
            # zakladne 2D grafy
            grafy_2d = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", 
                        "Box Plot", "Heatmap", "Pie Chart"]
            
            # 3D grafy len pre Matplotlib a Plotly
            grafy_3d = ["3D Scatter Plot", "3D Surface Plot", "3D Line Plot"]
            
        if kniznica in ["Matplotlib", "Plotly"]:
            dostupne_grafy = grafy_2d + grafy_3d
        else:
            dostupne_grafy = grafy_2d
        
        graf = st.selectbox(
            " Vyberte typ grafu:",
            dostupne_grafy
        )
        
        # info pre pouzivatela
        if kniznica not in ["Matplotlib", "Plotly"]:
            st.caption("Pre 3D grafy vyberte Matplotlib alebo Plotly")

        # vyber premennych podla typu grafu
        st.markdown("###  Nastavenie premenných")
            
        if graf in ["Scatter Plot", "Line Plot"]:
                stl1, stl2, stl3 = st.columns(3)
                with stl1:
                    xx = st.selectbox("X os:", numericke if numericke else sltpce)
                with stl2:
                    yy = st.selectbox("Y os:", numericke if numericke else sltpce)

        elif graf == "Bar Chart":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx= st.selectbox("Kategória:", kategorialne if kategorialne else sltpce)
                with stl2:
                    yy= st.selectbox("Hodnota:", numericke if numericke else sltpce)
            
        elif graf == "Histogram":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx= st.selectbox("Premenná:", numericke if numericke else sltpce)
                with stl2:
                    bins = st.slider("Počet binov:", 5, 100, 30)
                yy= None
            
        elif graf == "Box Plot":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx= st.selectbox("Kategória (voliteľné):", ["Žiadna"] + kategorialne)
                    xx= None if xx == "Žiadna" else xx
                with stl2:
                    yy= st.selectbox("Hodnota:", numericke if numericke else sltpce)
            
        elif graf == "Heatmap":
                sltp = st.multiselect("Vyberte premenné:", numericke, default=numericke[:5] if len(numericke) >= 5 else numericke)
                xx= yy = None
            
        elif graf == "Pie Chart":
                xx = st.selectbox("Kategória:", kategorialne if kategorialne else sltpce)
                yy = None

        if st.button(" Vygenerovať graf", type="primary", use_container_width=True):
            st.markdown(f"{graf} - {kniznica}")
            try:
                if kniznica == "Matplotlib":
                    fig, ax = plt.subplots(figsize=(12, 6))
                        
                    if graf == "Scatter Plot":
                            ax.scatter(df[xx], df[yy], alpha=0.6)
                            ax.set_xlabel(xx)
                            ax.set_ylabel(yy)
                        
                    elif graf == "Line Plot":
                            ax.plot(df[xx], df[yy])
                            ax.set_xlabel(xx)
                            ax.set_ylabel(yy)
                        
                    elif graf == "Bar Chart":
                            df.groupby(xx)[yy].mean().plot(kind='bar', ax=ax)
                            ax.set_xlabel(xx)
                            ax.set_ylabel(f"Priemer {yy}")

                    elif graf == "Histogram":
                            ax.hist(df[xx].dropna(), bins=bins)
                            ax.set_xlabel(xx)
                            ax.set_ylabel('')
                        
                    elif graf == "Box Plot":
                            if xx:
                                df.boxplot(column=yy, by=xx, ax=ax)
                            else:
                                df[yy].plot(kind='box',ax=ax)

                    elif graf == "Pie Chart":
                            df[xx].value_counts().plot(kind='pie', ax=ax)
                            ax.set_ylabel('')

                    plt.tight_layout() # automaticka oprava rozlozenia
                    st.pyplot(fig) # bez tohoto sa graf nevykresli

                elif kniznica == "Seaborn":
                    fig, ax = plt.subplots(figsize=(12,6))

                    if graf == "Scatter Plot":
                            sns.scatterplot(df=df, x=xx, y=yy, ax=ax)

                    elif graf == "Line Plot":
                            sns.lineplot(df=df,x=xx, y=yy, ax=ax)
                        
                    elif graf == "Bar Chart":
                            sns.barplot(df=df, x=xx, y=yy, ax=ax)

                    elif graf == "Histogram":
                            sns.histplot(df=df, x=xx, bins=bins, ax=ax)
                        
                    elif graf == "Box Plot":
                            sns.boxplot(df=df, x=xx, y=yy, ax=ax)

                    elif graf =="Heatmap":
                            if sltp:
                                corr = df[sltp].corr()
                                sns.heatmap(corr, annot=True, center=0, ax=ax)

                    plt.tight_layout() # automaticka oprava rozlozenia
                    st.pyplot(fig) # bez tohoto sa graf nevykresli

                elif kniznica == "Plotly":
                    if graf == "Scatter Plot":
                        fig = px.scatter(df, x=xx, y=yy)
                        
                    elif graf == "Line Plot":
                        fig = px.line(df, x=xx, y=yy)

                    elif graf == "Bar Chart":
                        fig = px.bar(df, x=xx, y=yy)

                    elif graf == "Histogram":
                        fig = px.histogram(df, x=xx, y=yy, nbins=bins)
                        
                    elif graf == "Box Plot":
                        fig = px.box(df, x=xx, y=yy)

            except Exception as e:
                    st.error(f" Chyba pri generovaní grafu: {str(e)}")
    except Exception as e:
                    st.error(f" Chyba pri generovaní grafu: {str(e)}")
        
