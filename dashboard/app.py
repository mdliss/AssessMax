"""Main Streamlit dashboard application"""

import streamlit as st

from auth import AuthManager
from config import settings

# Set page config FIRST before any other Streamlit commands
st.set_page_config(
    page_title=settings.dashboard_title,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for WCAG AA compliance and accessibility
st.markdown(
    """
    <style>
    /* WCAG AA Compliance */
    :root {
        --primary-color: #0066CC;
        --background-color: #FFFFFF;
        --secondary-bg: #F0F2F6;
        --text-color: #262730;
        --border-color: #E0E0E0;
    }

    /* Ensure sufficient contrast ratios */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-weight: 500;
        border: none;
        min-height: 44px; /* WCAG touch target size */
    }

    .stButton>button:hover {
        background-color: #0052A3;
        cursor: pointer;
    }

    .stButton>button:focus {
        outline: 3px solid #FFA500;
        outline-offset: 2px;
    }

    /* Keyboard navigation indicators */
    a:focus, button:focus, input:focus, select:focus, textarea:focus {
        outline: 3px solid #FFA500;
        outline-offset: 2px;
    }

    /* High contrast for text */
    .main p, .main li, .main span {
        color: var(--text-color);
        line-height: 1.6;
    }

    /* Skip to main content link */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--primary-color);
        color: white;
        padding: 8px;
        text-decoration: none;
        z-index: 100;
    }

    .skip-link:focus {
        top: 0;
    }

    /* Accessible tables */
    .dataframe {
        border: 1px solid var(--border-color);
    }

    .dataframe th {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
        padding: 12px;
        text-align: left;
    }

    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid var(--border-color);
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
    }

    /* Focus management for screen readers */
    [role="main"] {
        outline: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_login_page() -> None:
    """Display login page"""
    st.title("🔐 Login to AssessMax")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            st.write("Enter your credentials to access the dashboard")

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
    """Display main application after authentication"""

    # Sidebar navigation
    with st.sidebar:
        st.title("📊 AssessMax")

        # User info
        user_info = AuthManager.get_user_info()
        if user_info:
            st.write(f"**User:** {user_info.get('display_name', 'Educator')}")
            st.write(f"**Roles:** {', '.join(user_info.get('roles', ['educator']))}")
        else:
            st.write("**User:** Educator (Demo Mode)")
            st.write("**Roles:** educator")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            [
                "🏫 Class Overview",
                "👤 Student Detail",
                "📈 Trends",
                "📁 Uploads & Jobs",
            ],
            label_visibility="visible",
        )

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            AuthManager.logout()

    # Page routing
    if page == "🏫 Class Overview":
        from pages.class_overview import show_class_overview

        show_class_overview()
    elif page == "👤 Student Detail":
        from pages.student_detail import show_student_detail

        show_student_detail()
    elif page == "📈 Trends":
        from pages.trends import show_trends

        show_trends()
    elif page == "📁 Uploads & Jobs":
        from pages.uploads import show_uploads

        show_uploads()


def main() -> None:
    """Main application entry point"""
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


if __name__ == "__main__":
    main()
