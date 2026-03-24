import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict

class MoodVisualizer:
    def __init__(self):
        self.color_map = {
            'happy': '#FFD700',
            'sad': '#4169E1',
            'angry': '#DC143C',
            'anxious': '#9932CC',
            'neutral': '#808080'
        }

    def create_mood_timeline(self, mood_data: List[Dict]) -> px.Figure:
        """Creates an interactive timeline visualization of mood entries.

        Args:
            mood_data: List of dictionaries containing mood entries with
                      'timestamp', 'mood', and 'intensity' keys

        Returns:
            Plotly figure object with interactive mood timeline
        """
        df = pd.DataFrame(mood_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = px.line(df, 
                      x='timestamp',
                      y='intensity',
                      color='mood',
                      color_discrete_map=self.color_map,
                      title='Mood Timeline',
                      labels={
                          'timestamp': 'Date',
                          'intensity': 'Mood Intensity',
                          'mood': 'Emotion'
                      })

        fig.update_layout(
            hovermode='x unified',
            hoverlabel=dict(bgcolor='white'),
            legend_title_text='Emotions',
            plot_bgcolor='white'
        )

        return fig

    def generate_mood_summary(self, mood_data: List[Dict], days: int = 30) -> Dict:
        """Generates statistical summary of mood patterns.

        Args:
            mood_data: List of mood entry dictionaries
            days: Number of days to analyze

        Returns:
            Dictionary containing mood statistics and patterns
        """
        df = pd.DataFrame(mood_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter for specified time period
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff]

        summary = {
            'most_common_mood': df['mood'].mode().iloc[0],
            'average_intensity': round(df['intensity'].mean(), 2),
            'total_entries': len(df),
            'mood_distribution': df['mood'].value_counts().to_dict(),
            'peak_hours': df.groupby(df['timestamp'].dt.hour)['intensity'].mean().to_dict()
        }

        return summary

    def create_mood_heatmap(self, mood_data: List[Dict]) -> px.Figure:
        """Creates a heatmap showing mood patterns by day and hour.

        Args:
            mood_data: List of mood entry dictionaries

        Returns:
            Plotly figure object with mood heatmap
        """
        df = pd.DataFrame(mood_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()
        
        pivot_table = df.pivot_table(
            values='intensity',
            index='day',
            columns='hour',
            aggfunc='mean'
        )

        fig = px.imshow(pivot_table,
                        title='Mood Patterns by Day and Hour',
                        labels=dict(x='Hour of Day', y='Day of Week', color='Mood Intensity'),
                        aspect='auto',
                        color_continuous_scale='RdYlBu')

        return fig