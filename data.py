"""
data.py
A premium, interactive Streamlit dashboard for visualizing Movie Metadata
Now expanded to feature 10 robust visualizations!
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast

# ----------------------------------------------------
# 1. Dashboard Configuration & Premium Styling
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Movie Recommendation Dashboard",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more refined, premium "glassmorphism" feel
st.markdown("""
    <style>
    .reportview-container {
        background: #0e1117;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #e0e6ed;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="metric-container"] {
        background-color: #1a1c23;
        border: 1px solid #2e3039;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: transparent;
        padding: 0 1.5rem;
        color: #a0aec0;
    }
    .stTabs [aria-selected="true"] {
        color: #e0e6ed;
        border-bottom-color: #3b82f6 !important;
    }
    </style>
""", unsafe_allow_html=True)


# ----------------------------------------------------
# 2. Data Ingestion & Cleaning
# ----------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Loads movie metadata and applies robust preprocessing for visualization.
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

    # Drop missing critical data
    df = df.dropna(subset=['title', 'release_date', 'vote_average', 'vote_count'])
    
    # Clean Datetimes
    df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    df = df.dropna(subset=['release_year'])
    df['release_year'] = df['release_year'].astype(int)
    
    # Clean Numerics
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0)
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0)
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce').fillna(0)
    
    # Extract Primary Genre
    def extract_genre(genre_str):
        if pd.isna(genre_str):
            return "Unknown"
        try:
            genres = ast.literal_eval(genre_str)
            if isinstance(genres, list) and len(genres) > 0:
                return genres[0].get('name', 'Unknown')
        except (ValueError, SyntaxError):
            pass
        return "Unknown"

    df['primary_genre'] = df['genres'].apply(extract_genre)
    
    # Filter constraints (minimum votes to ensure fair ratings)
    df = df[df['vote_count'] > 100]
    
    return df

# Initialize Data
with st.spinner("Initializing Analytics Engine..."):
    df = load_and_clean_data('movies_metadata.csv')

if df.empty:
    st.warning("No data available to display. Please ensure 'movies_metadata.csv' is in the directory.")
    st.stop()


# ----------------------------------------------------
# 3. Sidebar Filtering Interface
# ----------------------------------------------------
st.sidebar.title("🎛️ Movie Filters")
st.sidebar.markdown("Refine the dataset to specific niches.")

min_year_bound = int(df['release_year'].min())
max_year_bound = int(df['release_year'].max())
selected_years = st.sidebar.slider(
    "Release Era (Years)",
    min_value=min_year_bound,
    max_value=max_year_bound,
    value=(1990, max_year_bound),
    step=1
)

available_genres = sorted(list(df['primary_genre'].unique()))
selected_genres = st.sidebar.multiselect(
    "Select Primary Genres",
    options=available_genres,
    default=available_genres[:5] if len(available_genres) > 5 else available_genres
)

min_rating = st.sidebar.number_input(
    "Minimum Rating (0-10)",
    min_value=0.0,
    max_value=10.0,
    value=6.0,
    step=0.5
)

mask = (
    (df['release_year'] >= selected_years[0]) & 
    (df['release_year'] <= selected_years[1]) &
    (df['vote_average'] >= min_rating) &
    (df['primary_genre'].isin(selected_genres if selected_genres else available_genres))
)
filtered_df = df[mask]
movie_search = st.text_input("🔍 Search Movie")

if movie_search:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(movie_search, case=False, na=False)
    ]

# ----------------------------------------------------
# 4. Main Dashboard Header & KPIs
# ----------------------------------------------------
st.title("🎬 AI Movie Recommendation Dashboard")
st.markdown("Dive into 10 advanced visualizations spanning financials, correlations, popularity, and genre statistics.")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(label="Total Films Analyzed", value=f"{len(filtered_df):,}")
with k2:
    avg_rating = filtered_df['vote_average'].mean() if not filtered_df.empty else 0
    st.metric(label="Average Rating", value=f"{avg_rating:.1f}/10")
with k3:
    budgeted = filtered_df[filtered_df['budget'] > 0]
    avg_budget = budgeted['budget'].mean() / 1e6 if not budgeted.empty else 0
    st.metric(label="Avg Budget (Millions)", value=f"${avg_budget:.1f}M")
with k4:
    profitable = filtered_df[filtered_df['revenue'] > 0]
    avg_rev = profitable['revenue'].mean() / 1e6 if not profitable.empty else 0
    st.metric(label="Avg Revenue (Millions)", value=f"${avg_rev:.1f}M")

st.markdown("---")

if filtered_df.empty:
    st.warning("Your filter criteria are too strict. No films found.")
    st.stop()


# ----------------------------------------------------
# 5. Core Visualizations (10 Graphs via Tabs)
# ----------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Overview & Financials", "🌟 Ratings & Popularity", "🔬 Deep Dive"])

# -------------- TAB 1: FINANCIALS --------------
with tab1:
    r1c1, r1c2 = st.columns(2)
    
    # Graph 1: Industry Output over Time
    with r1c1:
        st.subheader("1. Industry Output Over Time")
        yearly_counts = filtered_df.groupby('release_year').size().reset_index(name='film_count')
        fig_timeline = px.area(
            yearly_counts, x='release_year', y='film_count',
            color_discrete_sequence=['#3b82f6'],
            labels={'release_year': 'Year of Release', 'film_count': 'Number of Films'},
            template="plotly_dark"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
    # Graph 2: Budget vs Revenue Scatter
    with r1c2:
        st.subheader("2. Budget vs Box Office Revenue")
        valid_fin = filtered_df[(filtered_df['budget'] > 0) & (filtered_df['revenue'] > 0)]
        if not valid_fin.empty:
            fig_scatter = px.scatter(
                valid_fin, x='budget', y='revenue', color='vote_average',
                hover_name='title', size_max=15, opacity=0.7,
                color_continuous_scale=px.colors.sequential.Plasma,
                labels={'budget': 'Budget ($)', 'revenue': 'Revenue ($)'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Insufficient financial data.")

    r2c1, r2c2 = st.columns(2)
    
    # Graph 3: Average Financials Over Time
    with r2c1:
        st.subheader("3. Average Financials Era Trends")
        fin_yearly = filtered_df[(filtered_df['budget']>0) | (filtered_df['revenue']>0)].groupby('release_year')[['budget', 'revenue']].mean().reset_index()
        if not fin_yearly.empty:
            fig_fin_trends = px.line(
                fin_yearly, x='release_year', y=['budget', 'revenue'],
                labels={'value': 'Dollars ($)', 'variable': 'Metric', 'release_year': 'Year'},
                color_discrete_sequence=['#ef4444', '#10b981'],
                template="plotly_dark"
            )
            st.plotly_chart(fig_fin_trends, use_container_width=True)
        else:
            st.info("Insufficient financial data.")
            
    # Graph 4: Revenue by Top Genres (Box Plot)
    with r2c2:
        st.subheader("4. Revenue Distribution by Genre")
        top_g = filtered_df['primary_genre'].value_counts().head(5).index
        box_df = filtered_df[(filtered_df['primary_genre'].isin(top_g)) & (filtered_df['revenue'] > 0)]
        if not box_df.empty:
            fig_revenue_box = px.box(
                box_df, x='primary_genre', y='revenue', color='primary_genre',
                labels={'primary_genre': 'Genre', 'revenue': 'Revenue ($)'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_revenue_box, use_container_width=True)
        else:
            st.info("Insufficient genre/revenue data.")


# -------------- TAB 2: RATINGS & POPULARITY --------------
with tab2:
    r3c1, r3c2 = st.columns(2)
    
    # Graph 5: Genre Distribution Pie
    with r3c1:
        st.subheader("5. Overall Genre Composition")
        genre_counts = filtered_df['primary_genre'].value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        fig_pie = px.pie(
            genre_counts, names='Genre', values='Count', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
            template="plotly_dark"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Graph 6: Top 10 Rating Bar
    with r3c2:
        st.subheader("6. Top 10 Highest Rated Films")
        top10_df = filtered_df.sort_values(by=['vote_average', 'vote_count'], ascending=[False, False]).head(10)
        top10_df = top10_df.sort_values(by='vote_average', ascending=True)
        fig_bar = px.bar(
            top10_df, x='vote_average', y='title', orientation='h', color='vote_count',
            color_continuous_scale='Viridis',
            labels={'vote_average': 'Rating', 'title': '', 'vote_count': 'Total Votes'},
            template="plotly_dark"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    r4c1, r4c2 = st.columns(2)
    
    # Graph 7: Top 10 Popularity Bar
    with r4c1:
        st.subheader("7. Top 10 Most Popular Films")
        pop_df = filtered_df.sort_values(by='popularity', ascending=False).head(10)
        pop_df = pop_df.sort_values(by='popularity', ascending=True)
        fig_pop = px.bar(
            pop_df, x='popularity', y='title', orientation='h',
            color_discrete_sequence=['#f59e0b'],
            labels={'popularity': 'Popularity Score', 'title': ''},
            template="plotly_dark"
        )
        st.plotly_chart(fig_pop, use_container_width=True)
        
    # Graph 8: Rating vs Runtime Scatter
    with r4c2:
        st.subheader("8. Does Runtime Affect Rating?")
        valid_rt = filtered_df[filtered_df['runtime'] > 0]
        if not valid_rt.empty:
            fig_rt_rt = px.scatter(
                valid_rt, x='runtime', y='vote_average', color='primary_genre',
                hover_name='title', opacity=0.6,
                labels={'runtime': 'Runtime (Mins)', 'vote_average': 'Rating Average'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_rt_rt, use_container_width=True)
        else:
            st.info("Insufficient runtime data.")


# -------------- TAB 3: DEEP DIVE --------------
with tab3:
    r5c1, r5c2 = st.columns(2)
    
    # Graph 9: Runtime Distribution Histogram
    with r5c1:
        st.subheader("9. Distribution of Runtimes")
        valid_rt = filtered_df[filtered_df['runtime'] > 0]
        if not valid_rt.empty:
            fig_hist = px.histogram(
                valid_rt, x='runtime', nbins=50,
                color_discrete_sequence=['#8b5cf6'],
                labels={'runtime': 'Runtime (Mins)'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Insufficient runtime data.")
            
    # Graph 10: Top Languages Bar
    with r5c2:
        st.subheader("10. Most Common Original Languages")
        lang_counts = filtered_df['original_language'].value_counts().nlargest(10).reset_index()
        lang_counts.columns = ['Language', 'Count']
        fig_lang = px.bar(
            lang_counts, x='Language', y='Count',
            color_discrete_sequence=['#14b8a6'],
            template="plotly_dark"
        )
        st.plotly_chart(fig_lang, use_container_width=True)


# ----------------------------------------------------
# 6. Detailed Data Exploration
# ----------------------------------------------------
st.markdown("---")
st.subheader("🔍 Detailed Explorer")

view_cols = ['title', 'primary_genre', 'release_year', 'vote_average', 'vote_count', 'budget', 'revenue', 'popularity', 'runtime']
display_df = filtered_df[view_cols].rename(columns={
    'title': 'Title', 'primary_genre': 'Genre', 'release_year': 'Year',
    'vote_average': 'Rating', 'vote_count': 'Votes', 'budget': 'Budget ($)',
    'revenue': 'Revenue ($)', 'popularity': 'Popularity', 'runtime': 'Runtime (min)'
})

st.dataframe(display_df.head(200), use_container_width=True, height=350)
st.caption("Showing the top 200 matches according to selected filters.")
