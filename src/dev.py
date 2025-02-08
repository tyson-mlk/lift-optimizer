import asyncio
import streamlit as st

from sim.PAMultLift import main

st.title('Lift Optim (dev)')

asyncio.run(main())
