import streamlit as st
from app import process_pipeline

# Set up the web page
st.set_page_config(page_title="Secure AI Travel Assistant", page_icon="✈️")
st.title("✈️ Secure AI Travel Assistant")
st.markdown("Enter a destination to get a curated itinerary. This system is protected by hybrid static and dynamic LLM guardrails.")

# Create an input text box for the user
user_query = st.text_area("Where would you like to go?", placeholder="e.g., Plan a 3-day trip to Tokyo, Japan. Contact me at test@email.com")

# Create a submit button
if st.button("Generate Safe Itinerary"):
    if user_query.strip() == "":
        st.warning("Please enter a travel request.")
    else:
        with st.spinner("Analyzing request and checking guardrails..."):
            # Send the input to your existing backend pipeline
            result = process_pipeline(user_query)
            
            # Display the results based on the guardrail status
            if result.get("status") == "success":
                st.success("Guardrails Passed! Here is your itinerary:")
                
                # Format the JSON nicely into UI elements
                data = result["data"]
                st.subheader(f"📍 {data['destination']}, {data['country']}")
                
                st.write("**Recommended Attractions:**")
                for attraction in data['recommended_attractions']:
                    st.write(f"- {attraction}")
                    
                st.info(f"**Safety Note:** {data['safety_note']}")

              
            elif result.get("status") == "blocked":
                st.error("🚨 Request Blocked by Security Guardrails")
                st.write(f"**Reason:** {result.get('reason')}")
                
            else:
                st.warning("⚠️ System Fallback")
                st.write(f"**Reason:** {result.get('message')}")
                if "details" in result:
                    st.write(f"**Details:** {result.get('details')}")