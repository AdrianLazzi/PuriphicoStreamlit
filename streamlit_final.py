import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import streamlit as st

# Firebase configuration
if not firebase_admin._apps:
    cred = credentials.Certificate('cred.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://huntingtonhospital-default-rtdb.firebaseio.com/'
    })

# Function to read data from Firebase
def read_data_from_firebase():
    # Reference to the database location you want to access
    ref = db.reference('handwashing')
    data = ref.get()

    records = []
    for key, entry in data.items():
        records.append(entry)
        
    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def plot_histogram_by_unit(df, n_unit):
    plt.figure(figsize=(12, 8))
    bins = range(0, 30, 2)
  
    # Plot histogram for each unit with a different color
    #units = df['unit'].unique()
    #for unit in units:
    unit_data = df[df['unit'] == n_unit]
    plt.hist(unit_data['duration'], bins=bins, label=f'Unit {n_unit}', edgecolor='darkblue', color='#6495ED')

    # Adding titles and labels
    plt.title(f'Unit {n_unit}')
    plt.xlabel('Duration (seconds)')
    plt.xticks(ticks=bins, labels=[str(b) for b in bins])
    plt.ylabel('Number of Sessions')
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.grid(False)
    plt.tight_layout()

    # Display the plot in Streamlit
    st.pyplot(plt)

def get_session_state_for_unit(unit):
    key = f'led_on_{unit}'
    if key not in st.session_state:
        st.session_state[key] = get_led_state_from_firebase(unit)

def get_led_state_from_firebase(unit):
    ref = db.reference(f"/LED/{unit}")
    return ref.get()  # This directly returns the state (true/false) for the unit

def send_data_to_firebase(unit, state):
    ref = db.reference(f"/LED/{unit}")
    ref.set(state)  # This directly sets the state for the unit

def main():
    st.title("Huntington Hospital Handwashing Data")
    st.header(":blue[Powered by Puriphico]")
    st.sidebar.title("LED Feature Settings")

    df = read_data_from_firebase()

    units = [1, 2, 3, 4, 5]

    for unit in units:
        # Ensure the session state for each unit is initialized
        get_session_state_for_unit(unit)
        # Toggle button for LED state
        led_on = st.sidebar.toggle(f"Unit {unit}", value=st.session_state[f'led_on_{unit}'])

        if led_on:
            if not st.session_state[f'led_on_{unit}']:
                send_data_to_firebase(unit, True)
                st.session_state[f'led_on_{unit}'] = True
            st.sidebar.success(f"Unit {unit} LEDs are enabled")
        else:
            if st.session_state[f'led_on_{unit}']:
                send_data_to_firebase(unit, False)
                st.session_state[f'led_on_{unit}'] = False
            st.sidebar.warning(f"Unit {unit} LEDs are disabled")
    
    # Display data table
    st.subheader("All Data")
    st.dataframe(df)

    #average duration by unit
    average_duration_by_unit = df.groupby('unit')['duration'].mean()
    avg_duration_ledon = df[df['led_on'] == 1].groupby('unit')['duration'].mean()
    avg_duration_ledoff = df[df['led_on'] == 0].groupby('unit')['duration'].mean()
    total_samples_by_unit = df.groupby('unit').size()

    unit_df = pd.DataFrame({
        'sample size': total_samples_by_unit,
        'duration (LED on)': avg_duration_ledon,
        'duration (LED off)': avg_duration_ledoff,
        'duration (combined)': average_duration_by_unit
    }).reset_index()

    # Display the combined table
    st.subheader("Average Duration by Unit")
    st.table(unit_df)


    average_duration_by_loc = df.groupby('location')['duration'].mean()
    locavg_duration_ledon = df[df['led_on'] == 1].groupby('location')['duration'].mean()
    locavg_duration_ledoff = df[df['led_on'] == 0].groupby('location')['duration'].mean()
    total_samples_by_loc = df.groupby('location').size()

    location_df = pd.DataFrame({
        'sample size': total_samples_by_loc,
        'duration (LED on)': locavg_duration_ledon,
        'duration (LED off)': locavg_duration_ledoff,
        'duration (combined)': average_duration_by_loc
    }).reset_index()

    st.subheader("Average Duration by Location")
    st.table(location_df)

    st.subheader("Handwashing Duration Distribution by Unit")
    plot_histogram_by_unit(df, 1)
    plot_histogram_by_unit(df, 2)
    plot_histogram_by_unit(df, 3)
    plot_histogram_by_unit(df, 4)
    plot_histogram_by_unit(df, 5)

    # Plot data for each unit
    #st.subheader("Duration Over Time by Unit with Trendline")
    #plot_duration_with_trendline_by_unit(df)
    
    # Plot average duration by location
    #st.subheader("Average Duration by Location with Trendline")
    #plot_average_duration_with_trendline_by_location(df)

if __name__ == "__main__":
    main()



#unused after this -----------------------------------------------------------------------------------------------------


def plot_histogram_of_average_duration_by_unit(average_duration_by_unit):
    plt.figure(figsize=(10, 6))
    # Plot the histogram
    plt.bar(average_duration_by_unit.index, average_duration_by_unit.values, color='powderblue')
    # Labeling the histogram
    plt.title('Average Handwashing Duration by Unit')
    plt.xlabel('Unit')
    plt.ylabel('Average Duration (seconds)')
    plt.tight_layout()
    # Display the plot in Streamlit
    st.pyplot(plt)

def plot_average_duration_by_location(df):
    # Add a 'date' column to group by day
    df['date'] = df['timestamp'].dt.date
    
    # Group by date and location, then calculate the mean duration
    grouped = df.groupby(['date', 'location'])['duration'].mean().reset_index()
    
    # Pivot the table to make locations as columns
    pivot_table = grouped.pivot(index='date', columns='location', values='duration')
    
    # Plot the data
    pivot_table.plot(figsize=(12, 8), marker='o')
    plt.title('Grouped by Location')
    plt.xlabel('Date')
    plt.ylabel('Average Duration (seconds)')
    plt.xticks(rotation=45)
    plt.legend(title='Location')
    plt.tight_layout()
    st.pyplot(plt)

def plot_duration_by_unit(df):
    units = df['unit'].unique()
    
    for unit in units:
        unit_data = df[df['unit'] == unit].sort_values('timestamp')
        plt.figure(figsize=(10, 6))
        plt.plot(unit_data['timestamp'], unit_data['duration'], marker='o', linestyle='-')
        plt.title(f'Duration Over Time for Unit {unit}')
        plt.xlabel('Time')
        plt.ylabel('Duration (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


def plot_duration_with_trendline_by_unit(df):
    units = df['unit'].unique()
    
    for unit in units:
        unit_data = df[df['unit'] == unit].sort_values('timestamp')
        
        # Convert timestamps to ordinal format for trendline fitting
        x_values = unit_data['timestamp'].map(datetime.toordinal)
        y_values = unit_data['duration']

        # Perform linear regression to find the trendline
        slope, intercept = np.polyfit(x_values, y_values, 1)
        trendline = slope * x_values + intercept
        
        # Plot the data points and the trendline
        plt.figure(figsize=(10, 6))
        plt.scatter(unit_data['timestamp'], unit_data['duration'], label='Data Points', color='blue')
        plt.plot(unit_data['timestamp'], trendline, label='Trendline', color='red')
        plt.title(f'Duration Over Time for Unit {unit}')
        plt.xlabel('Time')
        plt.ylabel('Duration (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend()
        st.pyplot(plt)

