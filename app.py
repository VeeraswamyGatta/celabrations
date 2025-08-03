with tabs[0]:
    st.markdown("<h1 style='text-align: center; color: #E65100;'>Ganesh Chaturthi Sponsorship 2025</h1>", unsafe_allow_html=True)
    st.markdown("### 🙏 Choose one or more items to sponsor, or donate an amount of your choice.")

    name = st.text_input("👤 Full Name", key="name")
    email = st.text_input("📧 Email Address", key="email")
    apartment = st.text_input("🏢 Apartment Number (Required)", key="apartment")
    mobile = st.text_input("📱 Mobile Number (Optional)", key="mobile")

    st.markdown("---")
    st.markdown("### 🛕 Sponsorship Items")

    cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
    counts = dict(cursor.fetchall())

    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items ORDER BY id")
    rows = cursor.fetchall()

    selected_items = []
    for row in rows:
        item, cost, limit = row
        count = counts.get(item, 0)
        remaining = limit - count

        st.markdown(f"**{item}** — :orange[${cost}] | Total Limit: {limit}, Remaining: {remaining}")

        if remaining > 0:
            if st.checkbox(f"Sponsor {item}", key=item):
                selected_items.append(item)
        else:
            st.markdown(f"🚫 Fully Sponsored")
        st.markdown("---")

    st.markdown("### 💰 Donation")
    donation = st.number_input("Enter donation amount (optional)", min_value=0, value=0)

    if st.button("✅ Submit"):
        if not name.strip() or not email.strip() or not apartment.strip():
            st.error("❗ Name, Email, and Apartment Number are mandatory.")
        elif not selected_items and donation == 0:
            st.warning("Please sponsor at least one item or donate an amount.")
        else:
            try:
                if selected_items:
                    for idx, item in enumerate(selected_items):
                        don = donation if idx == 0 else 0
                        cursor.execute("""
                            INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (name, email, mobile, apartment, item, don))
                else:
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, NULL, %s)
                    """, (name, email, mobile, apartment, donation))
                conn.commit()
                st.success("🎉 Thank you for your contribution!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")
