import asyncio
import streamlit as st

from sim.PAMultLift import main

st.set_page_config(layout="wide")
st.title('Passenger Lift Movement State')

asyncio.run(main())
