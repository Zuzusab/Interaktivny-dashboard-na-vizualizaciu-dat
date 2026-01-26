import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from bokeh.plotting import figure
from bokeh.models import HoverTool
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
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
            
        if kniznica == "Seaborn":
            # Seaborn nepodporuje Pie Chart
            dostupne_grafy = [g for g in grafy_2d if g != "Pie Chart"]

        elif kniznica == "Matplotlib":
            # Matplotlib nepodporuje Heatmap
            dostupne_grafy = [g for g in grafy_2d if g != "Heatmap"]+ grafy_3d

        elif kniznica == "Plotly":
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
        
        elif graf in ["3D Scatter Plot", "3D Surface Plot", "3D Line Plot"]:
              stl1, stl2, stl3 = st.columns(3)
              with stl1:
                    xx = st.selectbox("Os X:", numericke if numericke else sltpce)
              with stl2:
                    yy = st.selectbox("Os Y:", numericke if numericke else sltpce)
              with stl3:
                    zz = st.selectbox("Os Z:", numericke if numericke else sltpce)
              if graf == "3D Line Plot":
                max_body = st.slider("Maximálny počet bodov:", 100, 5000, 1000, step=100)

        if st.button(" Vygenerovať graf", type="primary", use_container_width=True):
            st.markdown(f"{graf} - {kniznica}")
            try:
                if kniznica == "Matplotlib":
                    if graf in ["3D Scatter Plot", "3D Line Plot", "3D Surface Plot"]:
                          fig = plt.figure(figsize=(12,8))
                          ax = fig.add_subplot(111, projection = '3d')
                          
                          if graf == "3D Scatter Plot":
                                ax.scatter(df[xx], df[yy], df[zz])
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                                ax.set_zlabel(zz)

                          elif graf == "3D Line Plot":
                                st.warning("3D Line Plot je vhodný len pre usporiadané dáta s menej ako 500 bodmi.")
                                ax.plot(df[xx],df[yy], df[zz])
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                                ax.set_zlabel(zz)

                          elif graf == "3D Surface Plot":
                                data_clean = df[[xx, yy, zz]].dropna()
                                xi = np.linspace(data_clean[xx].min(), data_clean[xx].max(), 50)
                                yi = np.linspace(data_clean[yy].min(), data_clean[yy].max(), 50)
                                XI, YI = np.meshgrid(xi, yi)
                                ZI = griddata((data_clean[xx], data_clean[yy]), data_clean[zz], (XI, YI), method='cubic')
                                
                                surf = ax.plot_surface(XI, YI, ZI, cmap='viridis', alpha=0.8)
                                fig.colorbar(surf, ax=ax, shrink=0.5)
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                                ax.set_zlabel(zz)
                          plt.tight_layout() # automaticka oprava rozlozenia
                          st.pyplot(fig) # bez tohoto sa graf nevykresli
                    else:                
                        fig, ax = plt.subplots(figsize=(12, 6))
                            
                        if graf == "Scatter Plot":
                                ax.scatter(df[xx], df[yy], alpha=0.6)
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                            
                        elif graf == "Line Plot":
                                # agregacia dat - priemer pre kazdu hodnotu na X osi
                                df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                ax.plot(df_agg[xx], df_agg[yy])
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
                                sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                        elif graf == "Line Plot":
                                # agregacia dat - priemer pre kazdu hodnotu na X osi
                                df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
                            
                        elif graf == "Bar Chart":
                                sns.barplot(data=df, x=xx, y=yy, ax=ax)

                        elif graf == "Histogram":
                                sns.histplot(data=df, x=xx, bins=bins, ax=ax)
                            
                        elif graf == "Box Plot":
                                sns.boxplot(data=df, x=xx, y=yy, ax=ax)

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
                            # agregacia dat - priemer pre kazdu hodnotu na X osi
                            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                            fig = px.line(df_agg, x=xx, y=yy, markers=True)

                        elif graf == "Bar Chart":
                            fig = px.bar(df, x=xx, y=yy)

                        elif graf == "Histogram":
                            fig = px.histogram(df, x=xx, y=yy, nbins=bins)
                            
                        elif graf == "Box Plot":
                            fig = px.box(df, x=xx, y=yy)
                        
                        elif graf == "Heatmap":
                            if sltp:
                                    corr = df[sltp].corr()
                                    fig = px.imshow(corr, aspect = "auto")
                        
                        elif graf == "Pie Chart":
                            hodnoty = df[xx].value_counts()
                            fig = px.pie(values=hodnoty.values, names = hodnoty.index)
                        
                        # 3D Grafy
                        elif graf == "3D Scatter Plot":
                            fig = px.scatter_3d(df, x=xx, y=yy, z=zz)
                        
                        elif graf == "3D Line Plot":
                            if zz:
                                df_sorted = df.sort_values(by=xx)
                                fig = go.Figure(data=[go.Scatter3d(
                                    x=df_sorted[xx], 
                                    y=df_sorted[yy], 
                                    z=df_sorted[zz],
                                    mode='lines+markers',
                                    marker=dict(size=4),
                                    line=dict(width=2)
                                )])
                                fig.update_layout(title=f"3D Line Plot", scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz))
                            else:
                                st.warning("Pre 3D Line Plot musíte vybrať Z os!")

                        elif graf == "3D Surface Plot":
                            if zz:
                                # vytvorenie grid struktury pre surface plot
                                df_pivot = df.pivot_table(values=zz, index=yy, columns=xx, aggfunc='mean')
                                fig = go.Figure(data=[go.Surface(
                                    x=df_pivot.columns,
                                    y=df_pivot.index,
                                    z=df_pivot.values
                                )])
                                fig.update_layout(
                                    title=f"3D Surface Plot",
                                    scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz)
                                )
                            else:
                                st.warning("Pre 3D Surface Plot musíte vybrať Z os!")
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                    st.error(f" Chyba pri generovaní grafu: {str(e)}")
    except Exception as e:
                    st.error(f" Chyba pri generovaní grafu: {str(e)}")
        
