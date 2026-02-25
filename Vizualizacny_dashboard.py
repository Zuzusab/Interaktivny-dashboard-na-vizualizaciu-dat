import streamlit as st
import kaleido
import pandas as pd
import numpy as np
#fix pre Bokeh kompatibilitu
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool_
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from bokeh.plotting import figure
from bokeh.embed import components
import streamlit.components.v1 as components_st
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import altair as alt
import io
import base64
from scipy.interpolate import griddata
import vl_convert as vlc

def generate_chart(kniznica, graf, df, xx, yy, bins=None, sltp=None, zz=None, rozlisenie=100):

    shared_data = {}
    
    if kniznica == "Matplotlib":
        if graf in ["3D Surface Plot", "3D Wireframe Plot"]:
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
        
            if graf == "3D Surface Plot":
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

            elif graf == "3D Wireframe Plot":
                xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
                yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
                X, Y = np.meshgrid(xi, yi)
                
                points = np.column_stack((df[xx], df[yy]))
                values = df[zz]
                grid_points = np.column_stack((X.ravel(), Y.ravel()))
                Z = griddata(points, values, grid_points, method='cubic').reshape(X.shape)
                
                ax.plot_wireframe(X, Y, Z, color='darkblue', alpha=0.6, linewidth=0.5)
                ax.set_xlabel(xx)
                ax.set_ylabel(yy)
                ax.set_zlabel(zz)

            plt.tight_layout()
        else:                
            fig, ax = plt.subplots(figsize=(12, 6))
                    
            if graf == "Scatter Plot":
                ax.scatter(df[xx], df[yy], alpha=0.6)
                ax.set_xlabel(xx)
                ax.set_ylabel(yy)
            
            elif graf == "Line Plot":
                df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                ax.plot(df_agg[xx], df_agg[yy])
                ax.set_xlabel(xx)
                ax.set_ylabel(yy)
                
                shared_data['x_range'] = (df_agg[xx].min(), df_agg[xx].max())
                shared_data['y_range'] = (df_agg[yy].min(), df_agg[yy].max())
            
            elif graf == "Bar Chart":
                df.groupby(xx)[yy].mean().plot(kind='bar', ax=ax)
                ax.set_xlabel(xx)
                ax.set_ylabel(f"Priemer {yy}")

            elif graf == "Histogram":
                data_clean = df[xx].dropna()
                counts, bins_edges, patches = ax.hist(data_clean, bins=bins)
                ax.set_xlabel(xx)
                ax.set_ylabel('Počet')
                
                shared_data['y_max'] = counts.max() * 1.1
                shared_data['bin_edges'] = bins_edges
            
            elif graf == "Box Plot":
                if xx:
                    df.boxplot(column=yy, by=xx, ax=ax)
                else:
                    df[yy].plot(kind='box', ax=ax)

            elif graf == "Pie Chart":
                df[xx].value_counts().plot(kind='pie', ax=ax)
                ax.set_ylabel('')

            plt.tight_layout()
    
    elif kniznica == "Seaborn":
        fig, ax = plt.subplots(figsize=(12, 6))

        if graf == "Scatter Plot":
            sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

        elif graf == "Line Plot":
            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
            sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
            
            shared_data['y_range'] = (df_agg[yy].min(), df_agg[yy].max())
        
        elif graf == "Bar Chart":
            df_grouped = df.groupby(xx)[yy].mean().reset_index()
            ax.bar(df_grouped[xx], df_grouped[yy], edgecolor='black')
            ax.set_xlabel(xx)
            ax.set_ylabel(f"Priemer {yy}")
            plt.xticks(rotation=45)

        elif graf == "Histogram":
            data_clean = df[xx].dropna()
            min_val = data_clean.min()
            max_val = data_clean.max()
            bin_edges = np.linspace(min_val, max_val, bins + 1)
            counts, _, patches = ax.hist(data_clean, bins=bin_edges, edgecolor='black')
            ax.set_xlabel(xx)
            ax.set_ylabel('Počet')
            
            shared_data['bin_edges'] = bin_edges
        
        elif graf == "Box Plot":
            sns.boxplot(data=df, x=xx, y=yy, ax=ax)

        elif graf == "Heatmap":
            if sltp:
                corr = df[sltp].corr()
                sns.heatmap(corr, annot=True, center=0, ax=ax)

        plt.tight_layout()
    
    elif kniznica == "Plotly":
        if graf == "Scatter Plot":
            fig = px.scatter(df, x=xx, y=yy)
        
        elif graf == "Line Plot":
            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
            fig = px.line(df_agg, x=xx, y=yy, markers=True)

        elif graf == "Bar Chart":
            df_grouped = df.groupby(xx)[yy].mean().reset_index()
            fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")

        elif graf == "Histogram":
            data_clean = df[xx].dropna()
            min_val = float(data_clean.min())
            max_val = float(data_clean.max())
            bin_width = (max_val - min_val) / bins
            
            fig = px.histogram(df, x=xx, nbins=bins, range_x=[min_val, max_val])
            fig.update_layout(xaxis_title=xx, yaxis_title='Počet', bargap=0.1)
            fig.update_traces(xbins=dict(start=min_val, end=max_val, size=bin_width))
            
            if 'y_max' in shared_data:
                fig.update_yaxes(range=[0, shared_data['y_max']])
        
        elif graf == "Box Plot":
            fig = px.box(df, x=xx, y=yy)
        
        elif graf == "Heatmap":
            if sltp:
                corr = df[sltp].corr()
                fig = px.imshow(corr, aspect="auto")
        
        elif graf == "Pie Chart":
            hodnoty = df[xx].value_counts()
            fig = px.pie(values=hodnoty.values, names=hodnoty.index)
        
        elif graf == "3D Wireframe Plot":
            xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
            yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
            X, Y = np.meshgrid(xi, yi)
            
            points = np.column_stack((df[xx], df[yy]))
            values = df[zz]
            grid_points = np.column_stack((X.ravel(), Y.ravel()))
            Z = griddata(points, values, grid_points, method='cubic').reshape(X.shape)
            
            fig = go.Figure(data=[go.Surface(
                x=X, y=Y, z=Z,
                colorscale='Viridis',
                showscale=True,
                contours=dict(
                    z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project=dict(z=True))
                )
            )])
            fig.update_layout(
                scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz),
                height=600
            )

        elif graf == "3D Surface Plot":
            if zz:
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
    
    elif kniznica == "Bokeh":
        fig = figure(width=800, height=400, title=graf)
        
        if graf == "Scatter Plot":
            fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
        
        elif graf == "Line Plot":
            df_sorted = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
            
            if 'x_range' in shared_data and 'y_range' in shared_data:
                x_min, x_max = shared_data['x_range']
                y_min, y_max = shared_data['y_range']
                x_padding = (x_max - x_min) * 0.05
                y_padding = (y_max - y_min) * 0.05
                fig = figure(width=800, height=400, title=graf, 
                           x_range=(x_min - x_padding, x_max + x_padding),
                           y_range=(y_min - y_padding, y_max + y_padding))
            
            fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
        
        elif graf == "Bar Chart":
            grouped = df.groupby(xx)[yy].mean()
            fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
            fig.xaxis.ticker = list(range(len(grouped)))

        elif graf == "Histogram":
            hist, edges = np.histogram(df[xx].dropna(), bins=bins)
            fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
        
        fig.xaxis.axis_label = xx if xx else ""
        fig.yaxis.axis_label = yy if yy else ""
    
    elif kniznica == "Altair":
        if graf == "Scatter Plot":
            fig = alt.Chart(df).mark_circle(size=60, opacity=0.6).encode(
                x=alt.X(f'{xx}:Q', title=xx, scale=alt.Scale(zero=False)),
                y=alt.Y(f'{yy}:Q', title=yy, scale=alt.Scale(zero=False)),
                tooltip=[xx, yy]
            ).interactive()

        elif graf == "Line Plot":
            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
            
            # Ak nemáme zdieľané dáta, vypočítaj ich teraz
            if 'y_range' not in shared_data:
                shared_data['y_range'] = (df_agg[yy].min(), df_agg[yy].max())
            
            y_min, y_max = shared_data['y_range']
            y_padding = (y_max - y_min) * 0.1
            
            fig = alt.Chart(df_agg).mark_line(point=True).encode(
                x=alt.X(xx, title=xx),
                y=alt.Y(yy, title=yy, scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                tooltip=[xx, yy]
            ).interactive()

        elif graf == "Bar Chart":
            fig = alt.Chart(df).mark_bar().encode(
                x=alt.X(xx, title=xx),          
                y=alt.Y(f'mean({yy})', title=f"Priemer {yy}"), 
                tooltip=[xx, f'mean({yy})']
            ).interactive()
        
        elif graf == "Histogram":
            data_clean = df[xx].dropna()
            min_val = float(data_clean.min())
            max_val = float(data_clean.max())
            bin_width = (max_val - min_val) / bins
            
            fig = alt.Chart(df).mark_bar().encode(
                alt.X(f'{xx}:Q', 
                    bin=alt.Bin(step=bin_width, extent=[min_val, max_val]),
                    title=xx),
                y=alt.Y('count()', title='Počet'),
            ).interactive()
        
        elif graf == "Box Plot":
            fig = alt.Chart(df).mark_boxplot().encode(
                x=alt.X(f'{xx}:N', title=xx) if xx else alt.value(0),
                y=alt.Y(f'{yy}:Q', title=yy)
            )
        
        fig = fig.properties(width=800, height=400)
    
    return fig, shared_data

def display_chart(fig, kniznica):
    """Zobrazí graf podľa typu knižnice"""
    if kniznica in ["Matplotlib", "Seaborn"]:
        st.pyplot(fig)
    elif kniznica == "Plotly":
        st.plotly_chart(fig, use_container_width=True)
    elif kniznica == "Altair":
        st.altair_chart(fig, use_container_width=True)
    elif kniznica == "Bokeh":
        st.bokeh_chart(fig, use_container_width=True)

# konfiguracia stranky
st.set_page_config(page_title="Vizualizačný Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Inicializácia session state
if "fig" not in st.session_state:
    st.session_state.fig = None

if "graf_ready" not in st.session_state:
    st.session_state.graf_ready = False

if "kniznica_export" not in st.session_state:
    st.session_state.kniznica_export = None

if "graf_typ_export" not in st.session_state:
    st.session_state.graf_typ_export = None

def stiahnut_graf(fig, kniznica, format_suboru, nazov_grafu="graf"):
    try:
        buffer = io.BytesIO()
        
        if kniznica in ["Matplotlib", "Seaborn"]:
            # Matplotlib a Seaborn podporujú: PNG, PDF, SVG
            if format_suboru == "PNG":
                fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            elif format_suboru == "PDF":
                fig.savefig(buffer, format='pdf', bbox_inches='tight')
            elif format_suboru == "SVG":
                fig.savefig(buffer, format='svg', bbox_inches='tight')
        
                
        elif kniznica == "Plotly":
            if format_suboru == "PNG":
                fig_export = fig
                fig_export.update_layout(template="plotly")  # explicitný farebný template
                buffer = io.BytesIO(fig_export.to_image(format="png", engine="kaleido", scale=2))
            elif format_suboru == "PDF":
                fig_export = fig
                fig_export.update_layout(template="plotly")
                buffer = io.BytesIO(fig_export.to_image(format="pdf", engine="kaleido"))
            elif format_suboru == "SVG":
                fig_export = fig
                fig_export.update_layout(template="plotly")
                buffer = io.BytesIO(fig_export.to_image(format="svg", engine="kaleido"))
            elif format_suboru == "HTML":
                html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)
                buffer = io.BytesIO(html_str.encode("utf-8"))

                
        elif kniznica == "Altair":
            if format_suboru == "HTML":
                html_str = fig.to_html()
                buffer.write(html_str.encode())
            elif format_suboru == "PNG":
                try:
                    png_data = vlc.vegalite_to_png(fig.to_json())
                    buffer.write(png_data)
                except ImportError:
                    st.error("Nainštaluj vl-convert: pip install vl-convert-python")
                    return None
            elif format_suboru == "SVG":
                try:
                    svg_str = vlc.vegalite_to_svg(fig.to_json())
                    buffer.write(svg_str.encode())
                except ImportError:
                    st.error("Nainštaluj vl-convert: pip install vl-convert-python")
                    return None
            elif format_suboru == "JSON":
                json_str = fig.to_json()
                buffer.write(json_str.encode())
                
        elif kniznica == "Bokeh":
            from bokeh.io import export_png
            if format_suboru == "HTML":
                from bokeh.embed import file_html
                from bokeh.resources import CDN
                html_str = file_html(fig, CDN, nazov_grafu)
                buffer.write(html_str.encode())
            
        
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Chyba pri sťahovaní: {str(e)}")
        return None
    
Podporovane_formaty = {
    "Matplotlib": ["PNG", "PDF", "SVG"],
    "Seaborn": ["PNG", "PDF", "SVG"],
    "Plotly": ["HTML", "PNG", "SVG", "PDF"],
    "Bokeh": ["HTML"],
    "Altair": ["HTML", "PNG", "SVG", "JSON"]
}

st.markdown("""
    <style>
    [data-testid="stFileUploader"] div:first-child {
        font-size: 24px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.header(":violet[Interaktívny Vizualizačný Dashboard]")

subor = st.file_uploader(" Nahrajte dataset (CSV, Excel)", type=['csv', 'xlsx', 'xls'], help="Podporované formáty: CSV, Excel")

if subor is not None:
    try:
        if subor.name.endswith('.csv'):
            df = pd.read_csv(subor, sep=None, engine='python')
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
        
        with st.expander("Zobraziť dataset"):
            st.write(df.head(10))

        numericke = df.select_dtypes(include=['number']).columns.tolist()
        kategorialne = df.select_dtypes(include=['object']).columns.tolist()
        sltpce = df.columns.tolist()

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
                    ["Matplotlib", "Seaborn", "Plotly", "Bokeh", "Altair"], key="std_kniznica"
                )
        
            with stl2:
                grafy_2d = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", 
                            "Box Plot", "Heatmap", "Pie Chart"]
                grafy_3d = ["3D Surface Plot", "3D Wireframe Plot"]
                
            if kniznica == "Seaborn":
                dostupne_grafy = [g for g in grafy_2d if g != "Pie Chart"]

            elif kniznica == "Matplotlib":
                dostupne_grafy = [g for g in grafy_2d if g != "Heatmap"] + grafy_3d

            elif kniznica == "Plotly":
                dostupne_grafy = grafy_2d + grafy_3d

            elif kniznica == "Bokeh":
                dostupne_grafy = [g for g in grafy_2d if g not in ["Pie Chart", "Heatmap", "Box Plot"]]

            elif kniznica == "Altair":
                dostupne_grafy = [g for g in grafy_2d if g not in ["Pie Chart", "Heatmap"]]

            graf = st.selectbox(" Vyberte typ grafu:", dostupne_grafy, key="std_graf")
            
            if kniznica not in ["Matplotlib", "Plotly"]:
                st.caption("Pre 3D grafy vyberte Matplotlib alebo Plotly")

            st.markdown("###  Nastavenie premenných")
                
            if graf in ["Scatter Plot", "Line Plot"]:
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("X os:", numericke if numericke else sltpce, key="std_x")
                with stl2:
                    yy = st.selectbox("Y os:", numericke if numericke else sltpce, key="std_y")

            elif graf == "Bar Chart":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("Kategória:", kategorialne if kategorialne else sltpce, key="std_xx")
                with stl2:
                    yy = st.selectbox("Hodnota:", numericke if numericke else sltpce, key="std_yy")
            
            elif graf == "Histogram":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("Premenná:", numericke if numericke else sltpce, key="stdx")
                with stl2:
                    bins = st.slider("Počet binov:", 5, 100, 30, key="std_bins")
                yy = None
            
            elif graf == "Box Plot":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("Kategória (voliteľné):", ["Žiadna"] + kategorialne, key="stdxx")
                    xx = None if xx == "Žiadna" else xx
                with stl2:
                    yy = st.selectbox("Hodnota:", numericke if numericke else sltpce, key="stdyy")
            
            elif graf == "Heatmap":
                sltp = st.multiselect("Vyberte premenné:", numericke, default=numericke[:5] if len(numericke) >= 5 else numericke, key="stad_x")
                xx = yy = None
            
            elif graf == "Pie Chart":
                xx = st.selectbox("Kategória:", kategorialne if kategorialne else sltpce, key="stadx")
                yy = None
            
            elif graf in ["3D Surface Plot", "3D Wireframe Plot"]:
                stl1, stl2, stl3 = st.columns(3)
                with stl1:
                    xx = st.selectbox("Os X:", numericke if numericke else sltpce, key="stand_x")
                with stl2:
                    yy = st.selectbox("Os Y:", numericke if numericke else sltpce, key="stand_y")
                with stl3:
                    zz = st.selectbox("Os Z:", numericke if numericke else sltpce, key="stand_z")
                
                rozlisenie = st.slider("Rozlíšenie grafu:", 20, 200, 100, step=10, 
                                    help="Vyššie rozlíšenie = hladší graf, ale pomalší výpočet")

            if st.button(" Vygenerovať graf", type="primary", use_container_width=True, key="generovanie"):
                try:
                    fig = None
                    
                    if kniznica == "Matplotlib":
                        if graf in ["3D Surface Plot", "3D Wireframe Plot"]:
                            fig = plt.figure(figsize=(12, 8))
                            ax = fig.add_subplot(111, projection='3d')
                        
                            if graf == "3D Surface Plot":
                                data_clean = df[[xx, yy, zz]].dropna() #odstrani riadky kde je hodnota NaN
                                #vytvori mriezku
                                xi = np.linspace(data_clean[xx].min(), data_clean[xx].max(), 50)
                                yi = np.linspace(data_clean[yy].min(), data_clean[yy].max(), 50)
                                XI, YI = np.meshgrid(xi, yi)
                                ZI = griddata((data_clean[xx], data_clean[yy]), data_clean[zz], (XI, YI), method='cubic') #linearna interpolacia
                                # vykresli 3D plochu
                                surf = ax.plot_surface(XI, YI, ZI, cmap='viridis', alpha=0.8)
                                fig.colorbar(surf, ax=ax, shrink=0.5)
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                                ax.set_zlabel(zz)

                            elif graf == "3D Wireframe Plot":
                                xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
                                yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
                                X, Y = np.meshgrid(xi, yi)
                                Z = griddata((df[xx], df[yy]), df[zz], (X, Y), method='cubic')
                                
                                ax.plot_wireframe(X, Y, Z, color='darkblue', alpha=0.6, linewidth=0.5)
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                                ax.set_zlabel(zz)
                                         
                            plt.tight_layout()

                        else:                
                            fig, ax = plt.subplots(figsize=(12, 6))
                                
                            if graf == "Scatter Plot":
                                ax.scatter(df[xx], df[yy], alpha=0.6)
                                ax.set_xlabel(xx)
                                ax.set_ylabel(yy)
                            
                            elif graf == "Line Plot":
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
                                    df[yy].plot(kind='box', ax=ax)

                            elif graf == "Pie Chart":
                                df[xx].value_counts().plot(kind='pie', ax=ax)
                                ax.set_ylabel('')

                            plt.tight_layout()

                    elif kniznica == "Seaborn":
                        fig, ax = plt.subplots(figsize=(12, 6))

                        if graf == "Scatter Plot":
                            sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                        elif graf == "Line Plot":
                            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                            sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
                        
                        elif graf == "Bar Chart":
                            sns.barplot(data=df, x=xx, y=yy, ax=ax)

                        elif graf == "Histogram":
                            sns.histplot(data=df, x=xx, bins=bins, ax=ax)
                        
                        elif graf == "Box Plot":
                            sns.boxplot(data=df, x=xx, y=yy, ax=ax)

                        elif graf == "Heatmap":
                            if sltp:
                                sltp_num = df[sltp].select_dtypes(include=['number']).columns.tolist()
                                corr = df[sltp_num].corr()
                                sns.heatmap(corr, annot=True, fmt=".2f", center=0,
                                            cmap="RdBu_r", vmin=-1, vmax=1, ax=ax)
                            plt.tight_layout()

                    elif kniznica == "Plotly":
                        st.markdown("### Plotly")
                        if graf == "Scatter Plot":
                            fig = px.scatter(df, x=xx, y=yy)
                                
                        elif graf == "Line Plot":
                            df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                            fig = px.line(df_agg, x=xx, y=yy, markers=True)
                                
                        elif graf == "Bar Chart":
                            df_grouped = df.groupby(xx)[yy].mean().reset_index()
                            fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
                            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                            fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")
                                
                        elif graf == "Histogram":
                            data_clean = df[xx].dropna()
                            fig = px.histogram(df, x=xx, nbins=bins)

                        elif graf == "Box Plot":
                            fig = px.box(df, x=xx, y=yy)
                                
                        elif graf == "Pie Chart":
                            hodnoty = df[xx].value_counts()
                            fig = px.pie(values=hodnoty.values, names=hodnoty.index)

                        elif graf == "Heatmap":
                            if sltp:
                                corr = df[sltp].corr()
                                fig = px.imshow(corr, aspect = "auto")
                        
                        elif graf == "3D Wireframe Plot":
                            xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
                            yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
                            X, Y = np.meshgrid(xi, yi)
                            
                            # Oprava interpolácie
                            points = np.column_stack((df[xx], df[yy]))
                            values = df[zz]
                            grid_points = np.column_stack((X.ravel(), Y.ravel()))
                            Z = griddata(points, values, grid_points, method='cubic').reshape(X.shape)
                            
                            fig = go.Figure(data=[go.Surface(
                                x=X, y=Y, z=Z,
                                colorscale='Viridis',
                                showscale=True,
                                contours=dict(
                                    z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project=dict(z=True))
                                )
                            )])
                        elif graf == "3D Surface Plot":
                            if zz:
                                data_clean = df[[xx, yy, zz]].dropna()
                                xi = np.linspace(data_clean[xx].min(), data_clean[xx].max(), 50)
                                yi = np.linspace(data_clean[yy].min(), data_clean[yy].max(), 50)
                                XI, YI = np.meshgrid(xi, yi)
                                ZI = griddata(
                                    (data_clean[xx], data_clean[yy]), 
                                    data_clean[zz], 
                                    (XI, YI), 
                                    method='cubic'
                                )
                                fig = go.Figure(data=[go.Surface(
                                    x=XI, y=YI, z=ZI,
                                    colorscale='Viridis'
                                )])
                                fig.update_layout(
                                    title="3D Surface Plot",
                                    scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz),
                                    height=600
                                )
                            else:
                                st.warning("Pre 3D Surface Plot musíte vybrať Z os!")

                    elif kniznica == "Bokeh":
                        fig = figure(width=800, height=400, title=graf)
                        
                        if graf == "Scatter Plot":
                            fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
                        
                        elif graf == "Line Plot":
                            df_sorted = df.sort_values(by=xx)
                            fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
                        
                        elif graf == "Bar Chart":
                            grouped = df.groupby(xx)[yy].mean()
                            fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
                            fig.xaxis.ticker = list(range(len(grouped)))

                        elif graf == "Histogram":
                            hist, edges = np.histogram(df[xx].dropna(), bins=bins)
                            fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
                        
                        fig.xaxis.axis_label = xx if xx else ""
                        fig.yaxis.axis_label = yy if yy else ""

                    elif kniznica == "Altair":
                        if graf == "Scatter Plot":
                            fig = alt.Chart(df).mark_circle(size=60).encode(
                                x=xx, y=yy, tooltip=[xx, yy]
                            ).interactive()

                        elif graf == "Line Plot":
                            fig = alt.Chart(df).mark_line().encode(
                                x=xx, y=yy, tooltip=[xx, yy]
                            ).interactive()

                        elif graf == "Bar Chart":
                            fig = alt.Chart(df).mark_bar().encode(
                                x=xx, y=f'mean({yy})', tooltip=[xx, f'mean({yy})']
                            ).interactive()
                        
                        elif graf == "Histogram":
                            fig = alt.Chart(df).mark_bar().encode(
                                alt.X(f'{xx}:Q', bin=alt.Bin(maxbins=bins)),  #na os x ide numerická premenná
                                y='count()',   
                            ).interactive() 
                        
                        elif graf == "Box Plot":
                            fig = alt.Chart(df).mark_boxplot().encode(
                                x=f'{xx}:N' if xx else alt.value(0), #použije sa ako kategória (:N = nominal) na osi X alebo všetky hodnoty budú v jednom boxe (na pozícii 0)
                                y=f'{yy}:Q'
                            )
                        
                        fig = fig.properties(width=800, height=400)

                    # Uloženie grafu do session state
                    st.session_state.fig = fig
                    st.session_state.graf_ready = True
                    st.session_state.kniznica_export = kniznica
                    st.session_state.graf_typ_export = graf

                except Exception as e:
                    st.error(f" Chyba pri generovaní grafu: {str(e)}")
            
            # Zobrazenie grafu ak je ready 
            if st.session_state.graf_ready and st.session_state.fig is not None:
                st.markdown(f"### {st.session_state.graf_typ_export} - {st.session_state.kniznica_export}")
                if st.session_state.kniznica_export in ["Matplotlib", "Seaborn"]:
                    st.pyplot(st.session_state.fig)
                elif st.session_state.kniznica_export == "Plotly":
                    st.plotly_chart(st.session_state.fig, use_container_width=True, key=f"plotly_{st.session_state.graf_typ_export.replace(' ', '_')}")
                elif st.session_state.kniznica_export == "Altair":
                    st.altair_chart(st.session_state.fig, use_container_width=True)
                elif st.session_state.kniznica_export == "Bokeh":
                    script, div = components(st.session_state.fig)
                    components_st.html(f"""
                    <link rel="stylesheet" href="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.css">
                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.js"></script>
                    {script}
                    {div}
                    """, height=500)
                st.markdown("---")
                st.markdown("### Export grafu")

                col1, col2 = st.columns([2, 1])
                with col1:
                        format_export = st.selectbox(
                            "Vyberte formát exportu:",
                            Podporovane_formaty[st.session_state.kniznica_export],
                            key="format_selectbox"
                        )

                with col2:
                            if st.button("Uložiť graf", use_container_width=True):
                                buffer = stiahnut_graf(
                                    st.session_state.fig,
                                    st.session_state.kniznica_export,
                                    format_export,
                                    f"{st.session_state.graf_typ_export}_{st.session_state.kniznica_export}"
                                )

                                if buffer:
                                    mime_types = {
                                        "PNG": "image/png",
                                        "PDF": "application/pdf",
                                        "SVG": "image/svg+xml",
                                        "HTML": "text/html",
                                        "JSON": "application/json"
                                    }

                                    st.download_button(
                                        label=f"Stiahnuť ako {format_export}",
                                        data=buffer,
                                        file_name=f"{st.session_state.graf_typ_export.replace(' ', '_')}_{st.session_state.kniznica_export}.{format_export.lower()}",
                                        mime=mime_types.get(format_export, "application/octet-stream"),
                                        use_container_width=True
                                    )
                                    st.success(f"Graf pripravený na stiahnutie vo formáte {format_export}!")
         # Porovnávací režim                   
        else:  
            st.markdown("### Porovnanie vizualizačných knižníc") 
        
            kniznice = st.multiselect(
                " Vyberte knižnice na porovnanie:",
                ["Matplotlib", "Seaborn", "Plotly", "Bokeh", "Altair"], key="prvk"
            )
            
            if len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Plotly"}:
                dostupne_grafy = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot", 
                                "Pie Chart", "3D Surface Plot", "3D Wireframe Plot"]
                
            elif len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Bokeh"}:
                dostupne_grafy = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram"]
            
            elif len(kniznice) == 2 and set(kniznice) == {"Plotly", "Bokeh"}:
                dostupne_grafy = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram"]

            elif len(kniznice) == 2 and set(kniznice) == {"Altair", "Bokeh"}:
                dostupne_grafy = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram"]
            
            elif len(kniznice) >= 3:
                # spolocne grafy pre vsetky vybrane kniznice
                dostupne_pre_kniznice = {
                    "Matplotlib": ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot", "Pie Chart", "3D Surface Plot", "3D Wireframe Plot"],
                    "Seaborn": ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot", "Heatmap"],
                    "Plotly": ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot", "Heatmap", "Pie Chart", "3D Surface Plot", "3D Wireframe Plot"],
                    "Bokeh": ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram"],
                    "Altair": ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot"]
                }
                # priesecnik grafy podporovane vsetkymi vybranymi kniznicami
                dostupne_grafy = set(dostupne_pre_kniznice[kniznice[0]])
                for kniznica in kniznice[1:]:
                    dostupne_grafy = dostupne_grafy.intersection(set(dostupne_pre_kniznice[kniznica]))
                
                prioritne_poradie = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", 
                     "Box Plot", "Heatmap", "Pie Chart", 
                     "3D Surface Plot", "3D Wireframe Plot"]

                dostupne_grafy = [g for g in prioritne_poradie if g in dostupne_grafy]
            else:
                dostupne_grafy = ["Scatter Plot", "Line Plot", "Bar Chart", "Histogram", "Box Plot"]
            
            graf = st.selectbox(
                " Vyberte typ grafu na porovnanie:",
                dostupne_grafy, key="prvg"
            )
        
            bins = None
            sltp = None
            zz = None
            rozlisenie = 100

            # vyber premennych
            if graf in ["Scatter Plot", "Line Plot"]:
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("X os:", numericke if numericke else sltpce, key="prvx")
                with stl2:
                    yy = st.selectbox("Y os:", numericke if numericke else sltpce, key="prvy")
                
            elif graf == "Bar Chart":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("Kategória:", kategorialne if kategorialne else sltpce, key="prvxx")
                with stl2:
                    yy = st.selectbox("Hodnota:", numericke if numericke else sltpce, key="prvyy")
                
            elif graf == "Histogram":
                xx = st.selectbox("Premenná:", numericke if numericke else sltpce, key="prvh")
                bins = st.slider("Počet binov:", 5, 100, 30, key="prvb")
                yy = None
                
            elif graf == "Box Plot":
                stl1, stl2 = st.columns(2)
                with stl1:
                    xx = st.selectbox("Kategória (voliteľné):", ["Žiadna"] + kategorialne, key="porvx")
                    xx = None if xx == "Žiadna" else xx
                with stl2:
                    yy = st.selectbox("Hodnota:", numericke if numericke else sltpce, key="porvy")

            elif graf == "Heatmap":
                sltp = st.multiselect("Vyberte premenné:", numericke, default=numericke[:5] if len(numericke) >= 5 else numericke, key="prhx")
                xx = yy = None

            elif graf == "Pie Chart":
                xx = st.selectbox("Kategória:", kategorialne if kategorialne else sltpce, key="prpcx")
                yy = None

            elif graf in ["3D Surface Plot", "3D Wireframe Plot"]:
                stl1, stl2, stl3 = st.columns(3)
                with stl1:
                    xx = st.selectbox("Os X:", numericke if numericke else sltpce, key="prv3x")
                with stl2:
                    yy = st.selectbox("Os Y:", numericke if numericke else sltpce, key="pr3y")
                with stl3:
                    zz = st.selectbox("Os Z:", numericke if numericke else sltpce, key="pr3z")
                
                rozlisenie = st.slider("Rozlíšenie grafu:", 20, 200, 100, step=10, key="prvbin",
                                    help="Vyššie rozlíšenie = hladší graf, ale pomalší výpočet")
                
            if st.button(" Porovnať knižnice", use_container_width=True, key="prvgenerovanie"):
                if len(kniznice) < 2:
                    st.warning("Vyberte aspoň 2 knižnice na porovnanie")
                else:
                    # Implementácia porovnávacieho režimu 
                        if (len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Plotly"}):
                            
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None
                            if 'zz' not in locals():
                                zz = None
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Matplotlib":
                                stl_matplotlib = stl1
                                stl_plotly = stl2
                            else:
                                stl_matplotlib = stl2
                                stl_plotly = stl1
                            
                            with stl_matplotlib:
                                st.markdown("### Matplotlib")
                                
                                if graf in ["3D Surface Plot", "3D Wireframe Plot"]:
                                    fig = plt.figure(figsize=(12,8))
                                    ax = fig.add_subplot(111, projection='3d')
                                
                                    if graf == "3D Surface Plot":
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

                                    elif graf == "3D Wireframe Plot":
                                        # Vytvori mriežku
                                        xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
                                        yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
                                        X, Y = np.meshgrid(xi, yi)
                                        
                                        # Interpoluje Z hodnoty
                                        points = np.column_stack((df[xx], df[yy]))
                                        values = df[zz]
                                        grid_points = np.column_stack((X.ravel(), Y.ravel()))
                                        Z = griddata(points, values, grid_points, method='cubic').reshape(X.shape)
                                        
                                        # Vykresli wireframe
                                        ax.plot_wireframe(X, Y, Z, color='darkblue', alpha=0.6, linewidth=0.5, rstride=5, cstride=5)
                                        ax.set_xlabel(xx)
                                        ax.set_ylabel(yy)
                                        ax.set_zlabel(zz)

                                    plt.tight_layout()
                                    st.pyplot(fig)

                                else:                
                                    fig, ax = plt.subplots(figsize=(12, 6))
                                        
                                    if graf == "Scatter Plot":
                                        ax.scatter(df[xx], df[yy], alpha=0.6)
                                        ax.set_xlabel(xx)
                                        ax.set_ylabel(yy)
                                    
                                    elif graf == "Line Plot":
                                        df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                        ax.plot(df_agg[xx], df_agg[yy])
                                        ax.set_xlabel(xx)
                                        ax.set_ylabel(yy)
                                    
                                    elif graf == "Bar Chart":
                                        df_grouped = df.groupby(xx)[yy].mean()
                                        df_grouped.plot(kind='bar', ax=ax)
                                        ax.set_xlabel(xx)
                                        ax.set_ylabel(f"Priemer {yy}")
                                        
                                        # Ulož rozsah Y osi pre synchronizáciu
                                        y_max_bar = df_grouped.max() * 1.1
                                        ax.set_ylim(0, y_max_bar)

                                    elif graf == "Histogram":
                                        data_clean = df[xx].dropna()
                                        counts, bins_edges, patches = ax.hist(data_clean, bins=bins)
                                        ax.set_xlabel(xx)
                                        ax.set_ylabel('Počet')
                                        
                                        # Ulozi rozsah pre Plotly
                                        y_max = counts.max() * 1.1  # +10% rezerva
                                        ax.set_ylim(0, y_max)
                                    
                                    elif graf == "Box Plot":
                                        if xx:
                                            df.boxplot(column=yy, by=xx, ax=ax)
                                        else:
                                            df[yy].plot(kind='box', ax=ax)

                                    elif graf == "Pie Chart":
                                        df[xx].value_counts().plot(kind='pie', ax=ax)
                                        ax.set_ylabel('')

                                    plt.tight_layout()
                                    st.pyplot(fig)
                            
                            with stl_plotly:
                                st.markdown("### Plotly")
                                
                                if graf == "Scatter Plot":
                                    fig = px.scatter(df, x=xx, y=yy)
                                
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = px.line(df_agg, x=xx, y=yy, markers=True)
                                
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
                                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                                    fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")
                                    
                                    # Synchronizuj Y os s Matplotlib
                                    if 'y_max_bar' in locals():
                                        fig.update_yaxes(range=[0, y_max_bar])
                                
                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    fig = px.histogram(df, x=xx, nbins=bins)
                                    
                                    # Synchronizuje Y-os s Matplotlib
                                    # Ziska max hodnotu z Matplotlib
                                    fig.update_yaxes(range=[0, y_max])  # Pouzije rovnaku škálu
                                    fig.update_yaxes(title_text='Počet')
                                elif graf == "Box Plot":
                                    fig = px.box(df, x=xx, y=yy)
                                
                                elif graf == "Pie Chart":
                                    hodnoty = df[xx].value_counts()
                                    fig = px.pie(values=hodnoty.values, names=hodnoty.index)
                                
                                elif graf == "3D Wireframe Plot":
                                    # Vytvori mriežku
                                    xi = np.linspace(df[xx].min(), df[xx].max(), rozlisenie)
                                    yi = np.linspace(df[yy].min(), df[yy].max(), rozlisenie)
                                    X, Y = np.meshgrid(xi, yi)
                                    
                                    # Interpoluje Z hodnoty
                                    points = np.column_stack((df[xx], df[yy]))
                                    values = df[zz]
                                    grid_points = np.column_stack((X.ravel(), Y.ravel()))
                                    Z = griddata(points, values, grid_points, method='cubic').reshape(X.shape)
                                    
                                    # Vykresli wireframe v Plotly
                                    fig = go.Figure(data=[go.Surface(
                                        x=X, y=Y, z=Z,
                                        colorscale='Viridis',
                                        showscale=True,
                                        surfacecolor=Z,
                                        opacity=0.9,
                                        contours=dict(
                                            x=dict(show=True, color="darkblue", width=1),
                                            y=dict(show=True, color="darkblue", width=1),
                                            z=dict(show=False)
                                        )
                                    )])
                                    fig.update_layout(
                                        scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz),
                                        height=600
                                    )
                                
                                elif graf == "3D Surface Plot":
                                    if zz:
                                        data_clean = df[[xx, yy, zz]].dropna()
                                        xi = np.linspace(data_clean[xx].min(), data_clean[xx].max(), 50)
                                        yi = np.linspace(data_clean[yy].min(), data_clean[yy].max(), 50)
                                        XI, YI = np.meshgrid(xi, yi)
                                        ZI = griddata((data_clean[xx], data_clean[yy]), data_clean[zz], (XI, YI), method='cubic')
                                        
                                        fig = go.Figure(data=[go.Surface(x=XI, y=YI, z=ZI, colorscale='Viridis')])
                                        fig.update_layout(
                                            scene=dict(xaxis_title=xx, yaxis_title=yy, zaxis_title=zz),
                                            height=600
                                        )
                                    else:
                                        st.warning("Pre 3D Surface Plot musíte vybrať Z os!")
                                st.plotly_chart(fig, use_container_width=True)
                            
                        elif (len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Seaborn"}):
                            
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Matplotlib":
                                stl_matplotlib = stl1
                                stl_seaborn = stl2
                            else:
                                stl_matplotlib = stl2
                                stl_seaborn = stl1
                            
                            with stl_matplotlib:
                                st.markdown("### Matplotlib")
                                fig, ax = plt.subplots(figsize=(12, 6))
                                        
                                if graf == "Scatter Plot":
                                    ax.scatter(df[xx], df[yy], alpha=0.6)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    ax.plot(df_agg[xx], df_agg[yy])
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    
                                elif graf == "Bar Chart":
                                    df.groupby(xx)[yy].mean().plot(kind='bar', ax=ax)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")

                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    counts, bins_edges, patches = ax.hist(data_clean, bins=bins)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')

                                elif graf == "Box Plot":
                                        if xx:
                                            df.boxplot(column=yy, by=xx, ax=ax)
                                        else:
                                            df[yy].plot(kind='box', ax=ax)
                                plt.tight_layout()
                                st.pyplot(fig)
                            
                            with stl_seaborn:
                                    st.markdown("### Seaborn")
                                    fig, ax = plt.subplots(figsize=(12, 6))

                                    if graf == "Scatter Plot":
                                        sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                                    elif graf == "Line Plot":
                                        df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                        sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
                                    
                                    elif graf == "Bar Chart":
                                        sns.barplot(data=df, x=xx, y=yy, ax=ax)

                                    elif graf == "Histogram":
                                        sns.histplot(data=df, x=xx, bins=bins, ax=ax)
                                    
                                    elif graf == "Box Plot":
                                        sns.boxplot(data=df, x=xx, y=yy, ax=ax)

                                    elif graf == "Heatmap":
                                        if sltp:
                                            corr = df[sltp].corr()
                                            sns.heatmap(corr, annot=True, center=0, ax=ax)

                                    plt.tight_layout()
                                    st.pyplot(fig)
                        elif (len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Bokeh"}):
                            
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Matplotlib":
                                stl_matplotlib = stl1
                                stl_bokeh = stl2
                            else:
                                stl_matplotlib = stl2
                                stl_bokeh = stl1
                                # rozsahy osí pre Line Plot
                            if graf == "Line Plot":
                                df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                x_min, x_max = df_agg[xx].min(), df_agg[xx].max()
                                y_min, y_max = df_agg[yy].min(), df_agg[yy].max()
                                # 5% rezerva
                                x_padding = (x_max - x_min) * 0.05
                                y_padding = (y_max - y_min) * 0.05
                                x_range = (x_min - x_padding, x_max + x_padding)
                                y_range = (y_min - y_padding, y_max + y_padding)

                            with stl_matplotlib:
                                st.markdown("### Matplotlib")
                                fig, ax = plt.subplots(figsize=(12, 6))
                                        
                                if graf == "Scatter Plot":
                                    ax.scatter(df[xx], df[yy], alpha=0.6)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    ax.plot(df_agg[xx], df_agg[yy])
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    ax.set_xlim(x_range)
                                    ax.set_ylim(y_range)
                                    
                                elif graf == "Bar Chart":
                                    df.groupby(xx)[yy].mean().plot(kind='bar', ax=ax)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")

                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    counts, bins_edges, patches = ax.hist(data_clean, bins=bins)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')

                                plt.tight_layout()
                                st.pyplot(fig) 

                            with stl_bokeh:
                                st.markdown("### Bokeh")
                                fig = figure(width=800, height=400, title=graf)
                        
                                if graf == "Scatter Plot":
                                    fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
                                
                                elif graf == "Line Plot":
                                    df_sorted = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = figure(width=800, height=400, title=graf, x_range=x_range, y_range=y_range)
                                    fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
                                
                                elif graf == "Bar Chart":
                                    grouped = df.groupby(xx)[yy].mean()
                                    fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
                                    fig.xaxis.ticker = list(range(len(grouped)))

                                elif graf == "Histogram":
                                    hist, edges = np.histogram(df[xx].dropna(), bins=bins)
                                    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
                                
                                fig.xaxis.axis_label = xx if xx else ""
                                fig.yaxis.axis_label = yy if yy else ""
                                st.bokeh_chart(fig)
                        elif (len(kniznice) == 2 and set(kniznice) == {"Matplotlib", "Altair"}):
                            
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Matplotlib":
                                stl_matplotlib = stl1
                                stl_atlair = stl2
                            else:
                                stl_matplotlib = stl2
                                stl_atlair = stl1

                            with stl_matplotlib:
                                st.markdown("### Matplotlib")
                                fig, ax = plt.subplots(figsize=(12, 6))
                                        
                                if graf == "Scatter Plot":
                                    ax.scatter(df[xx], df[yy], alpha=0.6)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    
                                    # nastavi rozsahy osi
                                    x_min, x_max = df[xx].min(), df[xx].max()
                                    y_min, y_max = df[yy].min(), df[yy].max()
                                    x_padding = (x_max - x_min) * 0.05
                                    y_padding = (y_max - y_min) * 0.05
                                    
                                    ax.set_xlim([x_min - x_padding, x_max + x_padding])
                                    ax.set_ylim([y_min - y_padding, y_max + y_padding])
                                    
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    ax.plot(df_agg[xx], df_agg[yy])
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    
                                elif graf == "Bar Chart":
                                    df.groupby(xx)[yy].mean().plot(kind='bar', ax=ax)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")

                                elif graf == "Histogram":
                                    # Spoločné nastavenie binov
                                    data_clean = df[xx].dropna()
                                    min_val = float(data_clean.min())
                                    max_val = float(data_clean.max())
                                    bin_width = (max_val - min_val) / bins
                                    bin_edges = np.linspace(min_val, max_val, bins + 1)
                                    counts, _, patches = ax.hist(data_clean, bins=bin_edges, edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')

                                elif graf == "Box Plot":
                                        if xx:
                                            df.boxplot(column=yy, by=xx, ax=ax)
                                        else:
                                            df[yy].plot(kind='box', ax=ax)

                                plt.tight_layout()
                                st.pyplot(fig)  

                            with stl_atlair:
                                st.markdown("### Altair")  
                                if graf == "Scatter Plot":
                                    # ziska rozsahy osí z Matplotlib (ak existujú)
                                    x_min, x_max = df[xx].min(), df[xx].max()
                                    y_min, y_max = df[yy].min(), df[yy].max()
                                    
                                    # prida padding
                                    x_padding = (x_max - x_min) * 0.05
                                    y_padding = (y_max - y_min) * 0.05
                                    
                                    fig = alt.Chart(df).mark_circle(size=60, opacity=0.6).encode(
                                        x=alt.X(f'{xx}:Q', title=xx, 
                                                scale=alt.Scale(domain=[x_min - x_padding, x_max + x_padding])),
                                        y=alt.Y(f'{yy}:Q', title=yy, 
                                                scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                                        tooltip=[xx, yy]
                                    ).interactive()

                                if graf == "Line Plot":
                                    # agreguje data rovnako ako Matplotlib
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    
                                    # ak su zdielana rozsahy Y osi z Matplotlib
                                    if 'y_range' in locals():
                                        y_min, y_max = y_range
                                    else:
                                        y_min = df_agg[yy].min()
                                        y_max = df_agg[yy].max()
                                    
                                    y_padding = (y_max - y_min) * 0.1
                                    
                                    fig = alt.Chart(df_agg).mark_line(point=True).encode(
                                        x=alt.X(xx, title=xx),
                                        y=alt.Y(yy, title=yy, scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                                        tooltip=[xx, yy]
                                    ).interactive()

                                elif graf == "Bar Chart":
                                    fig = alt.Chart(df).mark_bar().encode(
                                        x=xx, y=f'mean({yy})', tooltip=[xx, f'mean({yy})']
                                    ).interactive()
                                
                                elif graf == "Histogram":
                                    # Vypočíta rovnaké hranice binov ako má Matplotlib
                                    data_clean = df[xx].dropna()
                                    min_val = float(data_clean.min())
                                    max_val = float(data_clean.max())
                                    
                                    fig = alt.Chart(df).mark_bar(stroke='white').encode(
                                        alt.X(f'{xx}:Q', 
                                            bin=alt.Bin(step=(max_val - min_val) / bins, 
                                                        extent=[min_val, max_val]),
                                            title=xx),
                                        y=alt.Y('count()', title='Počet'),
                                    ).interactive()
                                
                                elif graf == "Box Plot":
                                    fig = alt.Chart(df).mark_boxplot().encode(
                                        x=f'{xx}:N' if xx else alt.value(0), #použije sa ako kategória (:N = nominal) na osi X alebo všetky hodnoty budú v jednom boxe (na pozícii 0)
                                        y=f'{yy}:Q'
                                    )
                                st.altair_chart(fig, use_container_width=True)

                        elif (len(kniznice) == 2 and set(kniznice) == {"Seaborn", "Plotly"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Seaborn":
                                stl_seaborn = stl1
                                stl_plotly = stl2
                            else:
                                stl_seaborn = stl2
                                stl_plotly = stl1

                            with stl_seaborn:
                                st.markdown("### Seaborn")
                                fig, ax = plt.subplots(figsize=(12, 6))

                                if graf == "Scatter Plot":
                                    sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
                                    
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    ax.bar(df_grouped[xx], df_grouped[yy], edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")
                                    plt.xticks(rotation=45)

                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = data_clean.min()
                                    max_val = data_clean.max()
                                    bin_edges = np.linspace(min_val, max_val, bins + 1) # uprava binov aby obe mali rovnake
                                    counts, _, patches = ax.hist(data_clean, bins=bin_edges, edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')
                                    
                                elif graf == "Box Plot":
                                    sns.boxplot(data=df, x=xx, y=yy, ax=ax)

                                elif graf == "Heatmap":
                                    corr = df.corr(numeric_only=True)
                                    plt.figure(figsize=(10, 6))
                                    sns.heatmap(
                                        corr,
                                        annot=True,
                                        cmap="viridis"
                                    )

                                st.pyplot(plt)

                            with stl_plotly:
                                st.markdown("### Plotly")
                                if graf == "Scatter Plot":
                                    fig = px.scatter(df, x=xx, y=yy)
                                
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = px.line(df_agg, x=xx, y=yy, markers=True)
                                
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
                                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                                    fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")
                                
                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = float(data_clean.min())
                                    max_val = float(data_clean.max())
                                    bin_width = (max_val - min_val) / bins
                                    
                                    fig = px.histogram(df, x=xx, nbins=bins,
                                                    range_x=[min_val, max_val])
                                    fig.update_layout(
                                        xaxis_title=xx,
                                        yaxis_title='Počet',
                                        bargap=0.1
                                    )
                                    fig.update_traces(xbins=dict(
                                        start=min_val,
                                        end=max_val,
                                        size=bin_width
                                    ))
                                
                                elif graf == "Box Plot":
                                    fig = px.box(df, x=xx, y=yy)

                                elif graf == "Heatmap":
                                    if sltp:
                                        corr = df[sltp].corr()
                                        fig = px.imshow(corr, aspect = "auto")
                                    plt.tight_layout()

                                st.plotly_chart(fig, use_container_width=True)
                        elif (len(kniznice) == 2 and set(kniznice) == {"Seaborn", "Bokeh"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Seaborn":
                                stl_seaborn = stl1
                                stl_bokeh = stl2
                            else:
                                stl_seaborn = stl2
                                stl_bokeh = stl1

                            with stl_seaborn:
                                st.markdown("### Seaborn")
                                fig, ax = plt.subplots(figsize=(12, 6))

                                if graf == "Scatter Plot":
                                    sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    sns.lineplot(data=df_agg, x=xx, y=yy, ax=ax)
                                    
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    ax.bar(df_grouped[xx], df_grouped[yy], edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")
                                    plt.xticks(rotation=45)

                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = data_clean.min()
                                    max_val = data_clean.max()
                                    bin_edges = np.linspace(min_val, max_val, bins + 1) # uprava binov aby obe mali rovnake
                                    counts, _, patches = ax.hist(data_clean, bins=bin_edges, edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')

                                plt.tight_layout()
                                st.pyplot(fig)
                            
                            with stl_bokeh:
                                st.markdown("### Bokeh")
                                fig = figure(width=800, height=400, title=graf)
                        
                                if graf == "Scatter Plot":
                                    fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
                                
                                elif graf == "Line Plot":
                                    df_sorted = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = figure(width=800, height=400, title=graf)
                                    fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
                                
                                elif graf == "Bar Chart":
                                    grouped = df.groupby(xx)[yy].mean()
                                    fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
                                    fig.xaxis.ticker = list(range(len(grouped)))

                                elif graf == "Histogram":
                                    hist, edges = np.histogram(df[xx].dropna(), bins=bins)
                                    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
                                
                                fig.xaxis.axis_label = xx if xx else ""
                                fig.yaxis.axis_label = yy if yy else ""
                                st.bokeh_chart(fig)
                                
                        elif (len(kniznice) == 2 and set(kniznice) == {"Seaborn", "Altair"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Seaborn":
                                stl_seaborn = stl1
                                stl_altair = stl2
                            else:
                                stl_seaborn = stl2
                                stl_altair = stl1

                            with stl_seaborn:
                                st.markdown("### Seaborn")
                                fig, ax = plt.subplots(figsize=(12, 6))

                                if graf == "Scatter Plot":
                                    sns.scatterplot(data=df, x=xx, y=yy, ax=ax)

                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    # Získa rozsah Y osi
                                    y_min = df_agg[yy].min()
                                    y_max = df_agg[yy].max()
                                    y_padding = (y_max - y_min) * 0.1
                                    
                                    ax.plot(df_agg[xx], df_agg[yy], marker='o', linewidth=2)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(yy)
                                    ax.set_ylim([y_min - y_padding, y_max + y_padding])
                                    
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    ax.bar(df_grouped[xx], df_grouped[yy], edgecolor='black')
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel(f"Priemer {yy}")
                                    plt.xticks(rotation=45)

                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = data_clean.min()
                                    max_val = data_clean.max()
                                    bin_edges = np.linspace(min_val, max_val, bins + 1) # synchronizacia binov
                                    
                                    ax.hist(data_clean, bins=bin_edges)
                                    ax.set_xlabel(xx)
                                    ax.set_ylabel('Počet')

                                elif graf == "Box Plot":
                                    sns.boxplot(data=df, x=xx, y=yy, ax=ax)
                                    
                                plt.tight_layout()
                                st.pyplot(fig)

                            with stl_altair:
                                    st.markdown("### Altair")  
                                    if graf == "Scatter Plot":
                                        fig = alt.Chart(df).mark_circle(size=60).encode(
                                            x=xx, y=yy, tooltip=[xx, yy]
                                        ).interactive()

                                    elif graf == "Line Plot":
                                        df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                        # Získaj rozsah Y osi
                                        y_min = df_agg[yy].min()
                                        y_max = df_agg[yy].max()
                                        y_padding = (y_max - y_min) * 0.1
                                        
                                        fig = alt.Chart(df_agg).mark_line(point=True).encode(
                                            x=alt.X(xx, title=xx),
                                            y=alt.Y(yy, title=yy, scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                                            tooltip=[xx, yy]
                                        ).interactive()

                                    elif graf == "Bar Chart":
                                        fig = alt.Chart(df).mark_bar().encode(
                                            x=xx, y=f'mean({yy})', tooltip=[xx, f'mean({yy})']
                                        ).interactive()
                                    
                                    elif graf == "Histogram":
                                        # Vypočíta rovnaké hranice binov ako má Seaborn
                                        data_clean = df[xx].dropna()
                                        min_val = float(data_clean.min())
                                        max_val = float(data_clean.max())
                                        bin_width = (max_val - min_val) / bins
                                        
                                        fig = alt.Chart(df).mark_bar().encode(
                                            alt.X(f'{xx}:Q', 
                                                bin=alt.Bin(step=bin_width, extent=[min_val, max_val]),
                                                title=xx),
                                            y=alt.Y('count()', title='Počet'),
                                        ).interactive()
                                    
                                    elif graf == "Box Plot":
                                        fig = alt.Chart(df).mark_boxplot().encode(
                                            x=f'{xx}:N' if xx else alt.value(0), #použije sa ako kategória (:N = nominal) na osi X alebo všetky hodnoty budú v jednom boxe (na pozícii 0)
                                            y=f'{yy}:Q'
                                        )
                                    st.altair_chart(fig, use_container_width=True)

                        elif (len(kniznice) == 2 and set(kniznice) == {"Plotly", "Bokeh"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Plotly":
                                stl_plotly = stl1
                                stl_bokeh = stl2
                            else:
                                stl_plotly = stl2
                                stl_bokeh = stl1

                            with stl_plotly:
                                st.markdown("### Plotly")
                                if graf == "Scatter Plot":
                                    fig = px.scatter(df, x=xx, y=yy)
                                
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = px.line(df_agg, x=xx, y=yy, markers=True)
                                
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
                                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                                    fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")
                                
                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = float(data_clean.min())
                                    max_val = float(data_clean.max())
                                    bin_width = (max_val - min_val) / bins
                                    
                                    fig = px.histogram(df, x=xx, nbins=bins,
                                                    range_x=[min_val, max_val])
                                    fig.update_layout(
                                        xaxis_title=xx,
                                        yaxis_title='Počet',
                                        bargap=0.1
                                    )
                                    fig.update_traces(xbins=dict(
                                        start=min_val,
                                        end=max_val,
                                        size=bin_width
                                    ))
                                st.plotly_chart(fig, use_container_width=True)
                            with stl_bokeh:
                                st.markdown("### Bokeh")
                                fig = figure(width=800, height=400, title=graf)
                        
                                if graf == "Scatter Plot":
                                    fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
                                
                                elif graf == "Line Plot":
                                    df_sorted = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = figure(width=800, height=400, title=graf)
                                    fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
                                
                                elif graf == "Bar Chart":
                                    grouped = df.groupby(xx)[yy].mean()
                                    fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
                                    fig.xaxis.ticker = list(range(len(grouped)))

                                elif graf == "Histogram":
                                    hist, edges = np.histogram(df[xx].dropna(), bins=bins)
                                    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
                                
                                fig.xaxis.axis_label = xx if xx else ""
                                fig.yaxis.axis_label = yy if yy else ""
                                st.bokeh_chart(fig)       
                        elif (len(kniznice) == 2 and set(kniznice) == {"Plotly", "Altair"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None 
                    
                            stl1, stl2 = st.columns(2)
                            
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Plotly":
                                stl_plotly = stl1
                                stl_altair = stl2
                            else:
                                stl_plotly = stl2
                                stl_altair = stl1

                            with stl_plotly:
                                st.markdown("### Plotly")
                                if graf == "Scatter Plot":
                                    fig = px.scatter(df, x=xx, y=yy)
                                
                                elif graf == "Line Plot":
                                    df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = px.line(df_agg, x=xx, y=yy, markers=True)
                                
                                elif graf == "Bar Chart":
                                    df_grouped = df.groupby(xx)[yy].mean().reset_index()
                                    fig = px.bar(df_grouped, x=xx, y=yy, labels={yy: f"Priemer {yy}"}, text=yy)
                                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                                    fig.update_layout(xaxis_title=xx, yaxis_title=f"Priemer {yy}")
                                
                                elif graf == "Histogram":
                                    data_clean = df[xx].dropna()
                                    min_val = float(data_clean.min())
                                    max_val = float(data_clean.max())
                                    bin_width = (max_val - min_val) / bins
                                    
                                    fig = px.histogram(df, x=xx, nbins=bins,
                                                    range_x=[min_val, max_val])
                                    fig.update_layout(
                                        xaxis_title=xx,
                                        yaxis_title='Počet',
                                        bargap=0.1
                                    )
                                    fig.update_traces(xbins=dict(
                                        start=min_val,
                                        end=max_val,
                                        size=bin_width
                                    ))

                                elif graf == "Box Plot":
                                    fig = px.box(df, x=xx, y=yy)

                                st.plotly_chart(fig, use_container_width=True)
                            with stl_altair:
                                    st.markdown("### Altair")  
                                    if graf == "Scatter Plot":
                                        fig = alt.Chart(df).mark_circle(size=60, opacity=0.6).encode(
                                        x=alt.X(f'{xx}:Q', title=xx, scale=alt.Scale(zero=False)),
                                        y=alt.Y(f'{yy}:Q', title=yy, scale=alt.Scale(zero=False)),
                                        tooltip=[xx, yy]
                                    ).interactive()

                                    elif graf == "Line Plot":
                                        df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                        # Získaj rozsah Y osi
                                        y_min = df_agg[yy].min()
                                        y_max = df_agg[yy].max()
                                        y_padding = (y_max - y_min) * 0.1
                                        
                                        fig = alt.Chart(df_agg).mark_line(point=True).encode(
                                            x=alt.X(xx, title=xx),
                                            y=alt.Y(yy, title=yy, scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                                            tooltip=[xx, yy]
                                        ).interactive()

                                    elif graf == "Bar Chart":
                                        fig = alt.Chart(df).mark_bar().encode(
                                        x=alt.X(xx, title=xx),          
                                        y=alt.Y(f'mean({yy})', title=f"Priemer {yy}"), 
                                        tooltip=[xx, f'mean({yy})']
                                    ).interactive()
                                    
                                    elif graf == "Histogram":
                                        # Vypočíta rovnaké hranice binov ako má Seaborn
                                        data_clean = df[xx].dropna()
                                        min_val = float(data_clean.min())
                                        max_val = float(data_clean.max())
                                        bin_width = (max_val - min_val) / bins
                                        
                                        fig = alt.Chart(df).mark_bar().encode(
                                            alt.X(f'{xx}:Q', 
                                                bin=alt.Bin(step=bin_width, extent=[min_val, max_val]),
                                                title=xx),
                                            y=alt.Y('count()', title='Počet'),
                                        ).interactive()
                                    
                                    elif graf == "Box Plot":
                                        fig = alt.Chart(df).mark_boxplot().encode(
                                        x=alt.X(f'{xx}:N', title=xx),  
                                        y=alt.Y(f'{yy}:Q', title=yy))
                                    st.altair_chart(fig, use_container_width=True)

                        elif (len(kniznice) == 2 and set(kniznice) == {"Bokeh", "Altair"}):
                            # Inicializuj premenné ak neexistujú
                            if 'rozlisenie' not in locals():
                                rozlisenie = 100
                            if 'sltp' not in locals():
                                sltp = None
                        
                            stl1, stl2 = st.columns(2)
                                
                            # urcenie, ktora kniznica ide do ktoreho stlpca
                            if kniznice[0] == "Bokeh":
                                stl_bokeh = stl1
                                stl_altair = stl2
                            else:
                                stl_bokeh = stl2
                                stl_altair = stl1
                                
                            with stl_bokeh:
                                st.markdown("### Bokeh")
                                fig = figure(width=800, height=400, title=graf)
                        
                                if graf == "Scatter Plot":
                                    fig.scatter(df[xx].values, df[yy].values, size=8, alpha=0.6)
                                
                                elif graf == "Line Plot":
                                    df_sorted = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                    fig = figure(width=800, height=400, title=graf)
                                    fig.line(df_sorted[xx].values, df_sorted[yy].values, line_width=2)
                                
                                elif graf == "Bar Chart":
                                    grouped = df.groupby(xx)[yy].mean()
                                    fig.vbar(x=list(range(len(grouped))), top=grouped.values, width=0.8)
                                    fig.xaxis.ticker = list(range(len(grouped)))

                                elif graf == "Histogram":
                                    hist, edges = np.histogram(df[xx].dropna(), bins=bins)
                                    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], alpha=0.7)
                                
                                fig.xaxis.axis_label = xx if xx else ""
                                fig.yaxis.axis_label = yy if yy else ""
                                st.bokeh_chart(fig) 

                            with stl_altair:
                                    st.markdown("### Altair")  
                                    if graf == "Scatter Plot":
                                        fig = alt.Chart(df).mark_circle(size=60, opacity=0.6).encode(
                                        x=alt.X(f'{xx}:Q', title=xx, scale=alt.Scale(zero=False)),
                                        y=alt.Y(f'{yy}:Q', title=yy, scale=alt.Scale(zero=False)),
                                        tooltip=[xx, yy]
                                    ).interactive()

                                    elif graf == "Line Plot":
                                        df_agg = df.groupby(xx)[yy].mean().reset_index().sort_values(by=xx)
                                        # Získaj rozsah Y osi
                                        y_min = df_agg[yy].min()
                                        y_max = df_agg[yy].max()
                                        y_padding = (y_max - y_min) * 0.1
                                        
                                        fig = alt.Chart(df_agg).mark_line(point=True).encode(
                                            x=alt.X(xx, title=xx),
                                            y=alt.Y(yy, title=yy, scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding])),
                                            tooltip=[xx, yy]
                                        ).interactive()

                                    elif graf == "Bar Chart":
                                        fig = alt.Chart(df).mark_bar().encode(
                                        x=alt.X(xx, title=xx),          
                                        y=alt.Y(f'mean({yy})', title=f"Priemer {yy}"), 
                                        tooltip=[xx, f'mean({yy})']
                                    ).interactive()
                                    
                                    elif graf == "Histogram":
                                        # Vypočíta rovnaké hranice binov ako má Seaborn
                                        data_clean = df[xx].dropna()
                                        min_val = float(data_clean.min())
                                        max_val = float(data_clean.max())
                                        bin_width = (max_val - min_val) / bins
                                        
                                        fig = alt.Chart(df).mark_bar().encode(
                                            alt.X(f'{xx}:Q', 
                                                bin=alt.Bin(step=bin_width, extent=[min_val, max_val]),
                                                title=xx),
                                            y=alt.Y('count()', title='Počet'),
                                        ).interactive()
                                    st.altair_chart(fig, use_container_width=True)
                                    
                        else:  
                            # vytvori stlpce dynamicky podla poctu kniznic
                            cols = st.columns(len(kniznice))
                            # zdielanie dat pre synchronizaciu grafov
                            shared_data = {}
                            # prejde vsetky vybrane knižzice
                            for idx, kniznica in enumerate(kniznice):
                                with cols[idx]:
                                    st.markdown(f"### {kniznica}")
                                    
                                    try:
                                        # vygeneruje graf pomocou univerzalnej funkcie
                                        fig, chart_shared_data = generate_chart(
                                            kniznica=kniznica,
                                            graf=graf,
                                            df=df,
                                            xx=xx,
                                            yy=yy,
                                            bins=bins,
                                            sltp=sltp,
                                            zz=zz,
                                            rozlisenie=rozlisenie 
                                        )
                                        
                                        # aktualizuje zdielane data (prvy graf nastavi rozsahy)
                                        if idx == 0:
                                            shared_data.update(chart_shared_data)
                        
                                        # zobrazi graf
                                        display_chart(fig, kniznica)
                                        
                                    except Exception as e:
                                        st.error(f"Chyba pri generovaní {kniznica}: {str(e)}")
    except Exception as e:
        st.error(f" Chyba pri načítaní súboru: {str(e)}")