import streamlit as st
import pandas as pd
import soccerdata as sd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
from PIL import Image 

st.title("Football Recruitment Dashboard")
st.success("Packages imported successfully")