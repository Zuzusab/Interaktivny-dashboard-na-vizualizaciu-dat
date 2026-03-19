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
from scipy import stats
import altair as alt
import io
import base64
import vl_convert as vlc
from ydata_profiling import ProfileReport

def generate_chart(kniznica, graf, df, xx, yy, bins=None, sltp=None, zz=None, rozlisenie=100, shared_data=None):
    if shared_data is None:
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
            y_min = df[yy].min()
            y_max = df[yy].max()
            y_padding = (y_max - y_min) * 0.05
            fig = alt.Chart(df).mark_boxplot().encode(
                x=alt.X(f'{xx}:N', title=xx) if xx else alt.value(0),
                y=alt.Y(f'{yy}:Q', title=yy,
                        scale=alt.Scale(domain=[y_min - y_padding, y_max + y_padding]))
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

if "eda_html" not in st.session_state:
    st.session_state.eda_html = None

if "eda_ready" not in st.session_state:
    st.session_state.eda_ready = False

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
        # Odstránenie BOM znakov z názvov stĺpcov
        df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

        if "posledny_subor" not in st.session_state or st.session_state.posledny_subor != subor.name:
            st.session_state.posledny_subor = subor.name
            st.session_state.eda_ready = False
            st.session_state.eda_html = None
        
        numericke_raw = df.select_dtypes(include=['number']).columns.tolist()
        numericke = []
        kategorialne = df.select_dtypes(include=['object']).columns.tolist()
        id_stlpce = []
        for col in numericke_raw:
            n_unique = df[col].nunique()
            n_rows = len(df)
            col_clean = col.strip().replace('\ufeff', '')
            
            if 'id' in col_clean.lower() and n_unique == n_rows:
                id_stlpce.append(col)  # sleduje ID stĺpce
                continue
            elif n_unique <= 10 and (n_unique / n_rows) < 0.2:
                kategorialne.append(col)
            else:
                numericke.append(col)
        sltpce = df.columns.tolist()

        stl1, stl2, stl3, stl4 = st.columns(4)
        with stl1:
            st.metric("Počet riadkov", df.shape[0])
        with stl2:
            st.metric("Počet stĺpcov", df.shape[1])
        with stl3:
            st.metric("Numerické stĺpce", len(numericke))  # po preradení
        with stl4:
            st.metric("Kategoriálne stĺpce", len(kategorialne))  # po preradení
        if id_stlpce:
            st.caption(f" Ignorované ID stĺpce (vyradené z analýzy): {', '.join(id_stlpce)}")
        with st.expander("Zobraziť dataset"):
            st.write(df.head(10))
        with st.expander(" Automatický návrh grafov", expanded=True):
            navrhy = []

            n_num = len(numericke)
            n_kat = len(kategorialne)

            if n_num >= 1:
                navrhy.append({
                    "Typ premenných": "1 numerická premenná",
                    "Odporúčané grafy": "Histogram, Box Plot",
                    "Prečo": "Histogram ukáže rozdelenie hodnôt, Box Plot odhalí odľahlé hodnoty a štatistiky."
                })
            if n_num >= 2:
                navrhy.append({
                    "Typ premenných": "2 numerické premenné",
                    "Odporúčané grafy": "Scatter Plot, Line Plot",
                    "Prečo": "Scatter Plot ukáže vzťah medzi premennými, Line Plot vývoj v čase alebo poradí."
                })
            if n_num >= 3:
                navrhy.append({
                    "Typ premenných": "3+ numerické premenné",
                    "Odporúčané grafy": "Heatmap, 3D Surface Plot, 3D Wireframe Plot",
                    "Prečo": "Heatmap zobrazí korelácie medzi všetkými numerickými premennými naraz. 3D grafy ukážu vzťah troch premenných v priestore."
                })
            if n_kat >= 1:
                navrhy.append({
                    "Typ premenných": "1 kategoriálna premenná",
                    "Odporúčané grafy": "Pie Chart, Bar Chart",
                    "Prečo": "Pie Chart ukáže podiely kategórií, Bar Chart porovná ich početnosti alebo priemery."
                })
            if n_kat >= 1 and n_num >= 1:
                navrhy.append({
                    "Typ premenných": "1 kategoriálna + 1 numerická",
                    "Odporúčané grafy": "Bar Chart, Box Plot",
                    "Prečo": "Bar Chart porovná priemery skupín, Box Plot ukáže rozdelenie a outlineri v každej skupine."
                })

            if navrhy:
                st.markdown("Na základe tvojho datasetu odporúčam:")
                for n in navrhy:
                    st.markdown(f"**{n['Typ premenných']}** →  `{n['Odporúčané grafy']}`")
                    st.caption(n['Prečo'])
            else:
                st.info("Nepodarilo sa určiť typ premenných.")

        with st.expander(" Detekcia problémov v dátach"):
            problemy = []
            # Duplicitné riadky
            duplicity = df.duplicated().sum()
            if duplicity > 0:
                    problemy.append({"Stĺpec": "Celý dataset", "Typ problému": " Duplicitné riadky", 
                                "Detail": f"{duplicity} duplicitných riadkov"})
            for col in df.columns:
                # Chýbajúce hodnoty
                missing = df[col].isna().sum()
                missing_pct = missing / len(df) * 100
                if missing > 0:
                    problemy.append({"Stĺpec": col, "Typ problému": "Chýbajúce hodnoty", 
                                "Detail": f"{missing} hodnôt ({missing_pct:.1f}%)"})
                
                # Príliš veľa unikátov - nevhodné na Bar Chart
                if col in kategorialne and df[col].nunique() > 20:
                    problemy.append({"Stĺpec": col, "Typ problému": " Vysoká kardinalita", 
                                "Detail": f"{df[col].nunique()} unikátnych hodnôt — nevhodné na Bar Chart"})
                
                # Outlineri pre numerické stĺpce (IQR metóda)
                if col in numericke:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outlieri = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
                    if outlieri > 0:
                        problemy.append({"Stĺpec": col, "Typ problému": "Odľahlé hodnoty", 
                                    "Detail": f"{outlieri} outlinerov (IQR metóda)"})
            
            if problemy:
                st.dataframe(pd.DataFrame(problemy), use_container_width=True, hide_index=True)
            else:
                st.success(" Žiadne problémy nenájdené!")

        with st.expander(" EDA Report"):
            if st.button("Generovať EDA Report", type="primary"):
                with st.spinner("Generujem report... (môže trvať 10–30 sekúnd)"):
                    profile = ProfileReport(
                        df,
                        title="EDA Report",
                        explorative=True,
                        minimal=False
                    )
                    st.session_state.eda_html = profile.to_html()
                    st.session_state.eda_ready = True

            if st.session_state.get("eda_ready") and st.session_state.eda_html:
                st.download_button(
                    label=" Stiahnuť EDA Report (HTML)",
                    data=st.session_state.eda_html.encode("utf-8"),
                    file_name="eda_report.html",
                    mime="text/html",
                    use_container_width=True
                )
                components_st.html(st.session_state.eda_html, height=800, scrolling=True)

        mode = st.radio(" Vyberte režim vizualizácie:",["Štandardný režim", "Porovnávací režim"],horizontal=True )
        
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
            sltp = None
            zz = None
            bins = 30
            rozlisenie = 100
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
                    st.session_state["hist_xx"] = xx 
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
                            selection = alt.selection_point()
                            fig = alt.Chart(df).mark_circle(size=60).encode(
                                x=xx, y=yy, tooltip=[xx, yy],
                                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
                            ).add_params(selection).interactive()

                        elif graf == "Line Plot":
                            selection = alt.selection_point()
                            fig = alt.Chart(df).mark_line().encode(
                                x=xx, y=yy, tooltip=[xx, yy],
                                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
                            ).add_params(selection).interactive()

                        elif graf == "Bar Chart":
                            selection = alt.selection_point()
                            fig = alt.Chart(df).mark_bar().encode(
                                x=xx, y=f'mean({yy})', tooltip=[xx, f'mean({yy})'],
                                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
                            ).add_params(selection).interactive()
                        
                        elif graf == "Histogram":
                            selection = alt.selection_point()
                            fig = alt.Chart(df).mark_bar().encode(
                                alt.X(f'{xx}:Q', bin=alt.Bin(maxbins=bins)),
                                y='count()',
                                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
                            ).add_params(selection).interactive()

                        elif graf == "Box Plot":
                            fig = alt.Chart(df).mark_boxplot().encode(
                                x=f'{xx}:N' if xx else alt.value(0),
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
                if st.session_state.graf_typ_export in ["Scatter Plot", "Line Plot"]:
                    if xx in numericke and yy in numericke:
                        st.markdown("### Korelácia")
                        corr, p = stats.pearsonr(df[xx].dropna(), df[yy].dropna())
                        if p < 0.05:
                            st.info(f"**Pearsonova korelácia**: r = {corr:.3f}, p = {p:.4f} — štatisticky významná korelácia")
                        else:
                            st.info(f"**Pearsonova korelácia**: r = {corr:.3f}, p = {p:.4f} — korelácia nie je štatisticky významná")
                        st.caption("r blízko 1 alebo -1 = silná korelácia, r blízko 0 = slabá korelácia.")

                elif st.session_state.graf_typ_export == "Histogram":
                    hist_xx = st.session_state.get("hist_xx")
                    if not hist_xx:
                        hist_xx = xx  # záložný plán ak session state chýba
                    if hist_xx and hist_xx in numericke:
                        data = df[hist_xx].dropna()
                        st.markdown("### Analýza rozdelenia")
                        if len(data) >= 3 and len(data) <= 5000:
                            stat, p = stats.shapiro(data)
                            if p > 0.05:
                                st.success(f"**Shapiro-Wilk**: p = {p:.4f} — Normálne rozdelenie → odporúčané testy: **t-test, ANOVA**")
                            else:
                                st.warning(f"**Shapiro-Wilk**: p = {p:.4f} — Nie je normálne rozdelenie → odporúčané testy: **Mann-Whitney, Kruskal-Wallis**")
                            st.caption("Shapiro-Wilk testuje, či dáta pochádzajú z normálneho rozdelenia. p > 0.05 = normálne rozdelenie.")
                        elif len(data) > 5000:
                            st.info("Veľký dataset (>5000 hodnôt) — Shapiro-Wilk nie je spoľahlivý. Použite vizuálnu kontrolu Q-Q plotu.")
                        else:
                            st.warning("Príliš málo hodnôt pre Shapiro-Wilk test (min. 3).")

                        # Tlačidlo pre Q-Q plot
                        if "show_qq" not in st.session_state:
                            st.session_state.show_qq = False

                        if st.button(" Zobraziť Q-Q plot vedľa histogramu", key="qq_btn"):
                            st.session_state.show_qq = True

                        if st.session_state.show_qq:
                            col_hist, col_qq = st.columns(2)
                            with col_hist:
                                fig_h, ax_h = plt.subplots(figsize=(6, 4))
                                ax_h.hist(data, bins=st.session_state.get("std_bins", 30),
                                          edgecolor='black', color='steelblue', alpha=0.7)
                                ax_h.set_title(f"Histogram — {hist_xx}")
                                ax_h.set_xlabel(hist_xx)
                                ax_h.set_ylabel("Počet")
                                plt.tight_layout()
                                st.pyplot(fig_h)
                                plt.close(fig_h)
                            with col_qq:
                                fig_q, ax_q = plt.subplots(figsize=(6, 4))
                                stats.probplot(data, plot=ax_q)
                                ax_q.set_title(f"Q-Q plot — {hist_xx}")
                                plt.tight_layout()
                                st.pyplot(fig_q)
                                plt.close(fig_q)

                elif st.session_state.graf_typ_export == "Box Plot":
                    if yy and yy in numericke:
                        st.markdown("### Štatistické porovnanie skupín")
                        if xx and xx in kategorialne:
                            skupiny = df[xx].dropna().unique()
                            data_skupiny = [df[df[xx] == s][yy].dropna() for s in skupiny]

                            stats_data = []
                            for s, d in zip(skupiny, data_skupiny):
                                stats_data.append({
                                    "Skupina": s,
                                    "N": len(d),
                                    "Priemer": round(d.mean(), 3),
                                    "Medián": round(d.median(), 3),
                                    "Std": round(d.std(), 3)
                                })
                            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

                            if len(skupiny) == 2:
                                normalne = all(len(d) >= 3 and stats.shapiro(d)[1] > 0.05 for d in data_skupiny if len(d) >= 3)
                                if normalne:
                                    stat, p = stats.ttest_ind(*data_skupiny)
                                    test_nazov = "t-test"
                                    st.caption("Použitý t-test: normálne rozdelenie, 2 skupiny.")
                                else:
                                    stat, p = stats.mannwhitneyu(*data_skupiny)
                                    test_nazov = "Mann-Whitney U test"
                                    st.caption("Použitý Mann-Whitney U test: nie normálne rozdelenie, 2 skupiny.")
                                if p < 0.05:
                                    st.error(f"**{test_nazov}**: p = {p:.4f} — skupiny sa štatisticky významne líšia")
                                else:
                                    st.success(f"**{test_nazov}**: p = {p:.4f} — skupiny sa štatisticky významne nelíšia")

                            elif len(skupiny) > 2:
                                normalne = all(len(d) >= 3 and stats.shapiro(d)[1] > 0.05 for d in data_skupiny if len(d) >= 3)
                                if normalne:
                                    stat, p = stats.f_oneway(*data_skupiny)
                                    test_nazov = "ANOVA"
                                    st.caption("Použitá ANOVA: normálne rozdelenie, 3+ skupiny.")
                                else:
                                    stat, p = stats.kruskal(*data_skupiny)
                                    test_nazov = "Kruskal-Wallis test"
                                    st.caption("Použitý Kruskal-Wallis test: nie normálne rozdelenie, 3+ skupiny.")
                                if p < 0.05:
                                    st.error(f"**{test_nazov}**: p = {p:.4f} — medzi skupinami sú štatisticky významné rozdiely")
                                else:
                                    st.success(f"**{test_nazov}**: p = {p:.4f} — medzi skupinami nie sú štatisticky významné rozdiely")
                        else:
                            st.info("Pre porovnanie skupín vyber kategoriálnu premennú na osi X.")

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
            
            elif len(kniznice) >= 2:
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
                    cols = st.columns(len(kniznice))
                    shared_data = {}
                    for idx, kniznica in enumerate(kniznice):
                        with cols[idx]:
                            st.markdown(f"### {kniznica}")
                            try:
                                fig, chart_shared_data = generate_chart(
                                    kniznica=kniznica,
                                    graf=graf,
                                    df=df,
                                    xx=xx,
                                    yy=yy,
                                    bins=bins,
                                    sltp=sltp,
                                    zz=zz,
                                    rozlisenie=rozlisenie,
                                    shared_data=shared_data  # ← pridané
                                )
                                shared_data.update(chart_shared_data)  # ← zmazaná podmienka if idx == 0
                                display_chart(fig, kniznica)
                            except Exception as e:
                                st.error(f"Chyba pri generovaní {kniznica}: {str(e)}")
                        # Porovnanie skupín - automaticky pod grafmi
                if graf =="Box Plot" and yy and yy in numericke:
                    st.markdown("---")
                    st.markdown("### Štatistické porovnanie skupín")
                    
                    if xx and xx in kategorialne:
                        skupiny = df[xx].dropna().unique()
                        data_skupiny = [df[df[xx] == s][yy].dropna() for s in skupiny]
                        
                        # Základné štatistiky pre každú skupinu
                        stats_data = []
                        for s, d in zip(skupiny, data_skupiny):
                            stats_data.append({
                                "Skupina": s,
                                "N": len(d),
                                "Priemer": round(d.mean(), 3),
                                "Medián": round(d.median(), 3),
                                "Std": round(d.std(), 3)
                            })
                        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
                        
                        if len(skupiny) == 2:
                            normalne = all(len(d) >= 3 and stats.shapiro(d)[1] > 0.05 for d in data_skupiny if len(d) >= 3)
                            
                            if normalne:
                                stat, p = stats.ttest_ind(*data_skupiny)
                                test_nazov = "t-test"
                                st.caption("Použitý t-test: dáta majú normálne rozdelenie (Shapiro-Wilk p > 0.05) a porovnávame 2 skupiny.")
                            else:
                                stat, p = stats.mannwhitneyu(*data_skupiny)
                                test_nazov = "Mann-Whitney U test"
                                st.caption("Použitý Mann-Whitney U test: dáta nemajú normálne rozdelenie — neparametrická alternatíva k t-testu pre 2 skupiny.")
                            if p < 0.05:
                                st.error(f"**{test_nazov}**: p = {p:.4f} — skupiny sa **štatisticky významne líšia** (p < 0.05)")
                            else:
                                st.success(f"**{test_nazov}**: p = {p:.4f} — skupiny sa **štatisticky významne nelíšia** (p ≥ 0.05)")

                            # ✅ NOVÉ: Cohen's d pre 2 skupiny
                            d1, d2 = data_skupiny[0], data_skupiny[1]
                            pooled_std = np.sqrt((d1.std()**2 + d2.std()**2) / 2)
                            if pooled_std > 0:
                                cohens_d = (d1.mean() - d2.mean()) / pooled_std
                                abs_d = abs(cohens_d)
                                if abs_d < 0.2:
                                    efekt = "zanedbateľný"
                                    farba = "st.info"
                                elif abs_d < 0.5:
                                    efekt = "malý"
                                    farba = "st.info"
                                elif abs_d < 0.8:
                                    efekt = "stredný"
                                    farba = "st.warning"
                                else:
                                    efekt = "veľký"
                                    farba = "st.error"
                                
                                col_d1, col_d2 = st.columns(2)
                                with col_d1:
                                    st.metric("Cohen's d", f"{cohens_d:.3f}")
                                with col_d2:
                                    st.metric("Veľkosť efektu", efekt)
                                st.caption("Cohen's d meria veľkosť rozdielu medzi skupinami: |d| < 0.2 = zanedbateľný, 0.2–0.5 = malý, 0.5–0.8 = stredný, > 0.8 = veľký efekt.")
                        
                        elif len(skupiny) > 2:
                            normalne = all(len(d) >= 3 and stats.shapiro(d)[1] > 0.05 for d in data_skupiny if len(d) >= 3)
                            
                            if normalne:
                                stat, p = stats.f_oneway(*data_skupiny)
                                test_nazov = "ANOVA"
                                st.caption("Použitá ANOVA: dáta majú normálne rozdelenie a porovnávame 3 a viac skupín.")
                            else:
                                stat, p = stats.kruskal(*data_skupiny)
                                test_nazov = "Kruskal-Wallis test"
                                st.caption("Použitý Kruskal-Wallis test: dáta nemajú normálne rozdelenie — neparametrická alternatíva k ANOVA pre 3 a viac skupín.")
                            if p < 0.05:
                                st.error(f"**{test_nazov}**: p = {p:.4f} — medzi skupinami sú **štatisticky významné rozdiely** (p < 0.05)")
                            else:
                                st.success(f"**{test_nazov}**: p = {p:.4f} — medzi skupinami **nie sú štatisticky významné rozdiely** (p ≥ 0.05)")
                            
                            # ✅ NOVÉ: Eta² pre 3+ skupiny
                            celkovy_priemer = np.concatenate(data_skupiny).mean()
                            ss_between = sum(len(d) * (d.mean() - celkovy_priemer)**2 for d in data_skupiny)
                            ss_total = sum(((v - celkovy_priemer)**2) for d in data_skupiny for v in d)
                            if ss_total > 0:
                                eta2 = ss_between / ss_total
                                if eta2 < 0.01:
                                    efekt = "zanedbateľný"
                                elif eta2 < 0.06:
                                    efekt = "malý"
                                elif eta2 < 0.14:
                                    efekt = "stredný"
                                else:
                                    efekt = "veľký"
                                
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    st.metric("Eta²", f"{eta2:.3f}")
                                with col_e2:
                                    st.metric("Veľkosť efektu", efekt)
                                st.caption("Eta² meria podiel variancie vysvetlenej skupinami: < 0.01 = zanedbateľný, 0.01–0.06 = malý, 0.06–0.14 = stredný, > 0.14 = veľký efekt.")
                
                elif graf in ["Scatter Plot", "Line Plot"] and xx in numericke and yy in numericke:
                    st.markdown("---")
                    st.markdown("### Korelácia")
                    corr, p = stats.pearsonr(df[xx].dropna(), df[yy].dropna())
                    if p < 0.05:
                        st.info(f"**Pearsonova korelácia**: r = {corr:.3f}, p = {p:.4f} **štatisticky významná korelácia**")
                    else:
                        st.info(f"**Pearsonova korelácia**: r = {corr:.3f}, p = {p:.4f} korelácia **nie je štatisticky významná**")
                    st.caption("Pearsonova korelácia meria silu lineárneho vzťahu medzi dvoma numerickými premennými. r blízko 1 alebo -1 = silná korelácia, r blízko 0 = slabá korelácia.")
                
                elif graf == "Histogram" and xx and xx in numericke:
                    st.markdown("---")
                    st.markdown("### Analýza rozdelenia")
                    data = df[xx].dropna()
                    
                    if len(data) >= 3 and len(data) <= 5000:
                        stat, p = stats.shapiro(data)
                        if p > 0.05:
                            st.success(f"**Shapiro-Wilk**: p = {p:.4f} normálne rozdelenie odporúčané: **t-test, ANOVA**")
                            st.caption("Dáta majú normálne rozdelenie — môžeš použiť parametrické testy ktoré predpokladajú normalitu.")
                        else:
                            st.warning(f"**Shapiro-Wilk**: p = {p:.4f} nie je normálne rozdelenie odporúčané: **Mann-Whitney, Kruskal-Wallis**")
                            st.caption("Dáta nemajú normálne rozdelenie — použite neparametrické testy ktoré nekladú podmienky na rozdelenie.")
                    else:
                        st.info("Pre Shapiro-Wilkov test je potrebných 3–5000 hodnôt.")
    except Exception as e:
        st.error(f" Chyba pri načítaní súboru: {str(e)}")