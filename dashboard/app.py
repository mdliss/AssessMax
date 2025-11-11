"""Main Streamlit dashboard application."""

import streamlit as st

from auth import AuthManager
from components import inject_theme, render_footer, render_logo_badge
from config import settings

# Set page config FIRST before any other Streamlit commands
st.set_page_config(
    page_title=settings.dashboard_title,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()


def show_login_page() -> None:
    """Display login page."""

    render_logo_badge("Educator Access", "Secure Cognito-backed sign in")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form", clear_on_submit=True):
            st.markdown(
                """
                <div class="pulse-card drop-in">
                    <div class="pulse-subheading">Authentication</div>
                    <div class="pulse-metric-value">Welcome Back</div>
                    <p>Enter your credentials to continue to the PulseMax command center.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            username = st.text_input(
                "Username",
                help="Your educator username",
                label_visibility="visible",
            )

            password = st.text_input(
                "Password",
                type="password",
                help="Your password",
                label_visibility="visible",
            )

            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if AuthManager.login(username, password):
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")

        st.info(
            """
            **Demo Credentials (Development Mode)**
            - Username: Any non-empty string
            - Password: Any non-empty string
            """
        )


def show_main_app() -> None:
    """Display main application after authentication."""

    # Sidebar navigation
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-logo">
                <span>PULSEMAX</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='pulse-divider'></div>", unsafe_allow_html=True)

        # User info
        user_info = AuthManager.get_user_info()
        if user_info:
            st.markdown(
                f"**{user_info.get('display_name', 'Educator')}**<br>"
                f"<span class='pulse-subheading'>Roles · {', '.join(user_info.get('roles', ['educator']))}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "**Educator (Demo Mode)**<br><span class='pulse-subheading'>Roles · educator</span>",
                unsafe_allow_html=True,
            )

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            [
                "Class Overview",
                "Student Detail",
                "Trends",
                "Uploads & Jobs",
            ],
            label_visibility="visible",
        )

        st.divider()

        if st.button("Logout", use_container_width=True):
            AuthManager.logout()

    # Page routing
    if page == "Class Overview":
        from views.class_overview import show_class_overview

        show_class_overview()
    elif page == "Student Detail":
        from views.student_detail import show_student_detail

        show_student_detail()
    elif page == "Trends":
        from views.trends import show_trends

        show_trends()
    elif page == "Uploads & Jobs":
        from views.uploads import show_uploads

        show_uploads()


def main() -> None:
    """Main application entry point."""

    # Add skip to main content link for accessibility
    st.markdown(
        '<a href="#main-content" class="skip-link">Skip to main content</a>',
        unsafe_allow_html=True,
    )

    # Main content area
    st.markdown('<main id="main-content" role="main" tabindex="-1">', unsafe_allow_html=True)

    if not AuthManager.is_authenticated():
        show_login_page()
    else:
        show_main_app()

    st.markdown("</main>", unsafe_allow_html=True)
    render_footer()


if __name__ == "__main__":
    main()
