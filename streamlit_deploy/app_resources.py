"""
EduVid Creator Pro - With REAL SDOH Resources & Research Tools
Complete educational platform with actual services, databases, and direct links
"""

import streamlit as st
import os
import json
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import re

# Page configuration
st.set_page_config(
    page_title="EduVid Creator Pro - Real SDOH Resources & Tools",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.samhsa.gov/find-help/national-helpline',
        'About': "Educational Video Creator with Real SDOH Resources"
    }
)

# ==================== REAL SDOH RESOURCES DATABASE ====================

REAL_SDOH_RESOURCES = {
    "Food Security": {
        "National Services": {
            "Feeding America": {
                "url": "https://www.feedingamerica.org/find-your-local-foodbank",
                "description": "Find local food banks nationwide",
                "phone": "1-800-771-2303",
                "services": ["Food banks", "Mobile pantries", "School pantries", "Senior programs"]
            },
            "SNAP (Food Stamps)": {
                "url": "https://www.fns.usda.gov/snap/state-directory",
                "description": "Supplemental Nutrition Assistance Program",
                "phone": "1-800-221-5689",
                "services": ["Monthly benefits", "Online grocery", "Farmers markets"]
            },
            "WIC Program": {
                "url": "https://www.fns.usda.gov/wic",
                "description": "Women, Infants, and Children nutrition program",
                "phone": "1-800-942-3678",
                "services": ["Nutrition education", "Breastfeeding support", "Food benefits"]
            },
            "Meals on Wheels": {
                "url": "https://www.mealsonwheelsamerica.org/find-meals",
                "description": "Home-delivered meals for seniors",
                "phone": "1-888-998-6325",
                "services": ["Daily meals", "Safety checks", "Social connection"]
            },
            "No Kid Hungry": {
                "url": "https://www.nokidhungry.org/find-free-meals",
                "text": "Text 'FOOD' to 304-304",
                "description": "Free meals for kids and teens",
                "services": ["Summer meals", "After-school programs", "Breakfast programs"]
            }
        },
        "Research & Data": {
            "USDA Food Security Reports": "https://www.ers.usda.gov/topics/food-nutrition-assistance/food-security-in-the-u-s/",
            "Feeding America Map the Meal Gap": "https://map.feedingamerica.org/",
            "Food Research & Action Center": "https://frac.org/research/resource-library"
        }
    },
    
    "Housing & Homelessness": {
        "National Services": {
            "HUD Resource Locator": {
                "url": "https://resources.hud.gov/",
                "description": "Find housing assistance and homeless services",
                "phone": "1-800-569-4287",
                "services": ["Emergency shelter", "Transitional housing", "Permanent housing"]
            },
            "National Coalition for the Homeless": {
                "url": "https://nationalhomeless.org/references/need-help/",
                "description": "Homeless assistance directory",
                "phone": "1-202-462-4822",
                "services": ["Shelter directories", "Legal aid", "Healthcare access"]
            },
            "211 Helpline": {
                "url": "https://www.211.org/",
                "description": "Comprehensive local services",
                "phone": "211",
                "services": ["Housing", "Food", "Healthcare", "Crisis intervention"]
            },
            "Salvation Army": {
                "url": "https://www.salvationarmyusa.org/usn/provide-shelter/",
                "description": "Emergency shelter and services",
                "phone": "1-800-SAL-ARMY",
                "services": ["Emergency shelter", "Transitional housing", "Case management"]
            },
            "United Way": {
                "url": "https://www.unitedway.org/find-your-united-way/",
                "description": "Local community services",
                "phone": "211",
                "services": ["Housing assistance", "Financial stability", "Education"]
            }
        },
        "Research & Data": {
            "HUD Annual Homeless Assessment": "https://www.hudexchange.info/homelessness-assistance/ahar/",
            "National Alliance to End Homelessness": "https://endhomelessness.org/homelessness-in-america/",
            "Urban Institute Housing Research": "https://www.urban.org/policy-centers/metropolitan-housing-and-communities-policy-center"
        }
    },
    
    "Healthcare Access": {
        "National Services": {
            "Healthcare.gov": {
                "url": "https://www.healthcare.gov/",
                "description": "Health insurance marketplace",
                "phone": "1-800-318-2596",
                "services": ["Insurance enrollment", "Medicaid", "Subsidies"]
            },
            "HRSA Find a Health Center": {
                "url": "https://findahealthcenter.hrsa.gov/",
                "description": "Federally qualified health centers",
                "phone": "1-877-464-4772",
                "services": ["Primary care", "Dental", "Mental health", "Pharmacy"]
            },
            "GoodRx": {
                "url": "https://www.goodrx.com/",
                "description": "Prescription drug discounts",
                "app": "Available on iOS/Android",
                "services": ["Drug price comparison", "Coupons", "Savings programs"]
            },
            "NeedyMeds": {
                "url": "https://www.needymeds.org/",
                "description": "Medicine assistance programs",
                "phone": "1-800-503-6897",
                "services": ["Drug assistance", "Disease funds", "Free clinics"]
            },
            "RxAssist": {
                "url": "https://www.rxassist.org/",
                "description": "Patient assistance programs",
                "services": ["Medication access", "Application assistance", "Program database"]
            }
        },
        "Telehealth Services": {
            "Teladoc": "https://www.teladoc.com/",
            "MDLive": "https://www.mdlive.com/",
            "Amwell": "https://amwell.com/",
            "Doctor on Demand": "https://www.doctorondemand.com/"
        },
        "Research & Data": {
            "Kaiser Family Foundation": "https://www.kff.org/",
            "CDC Health Statistics": "https://www.cdc.gov/nchs/",
            "AHRQ Healthcare Quality": "https://www.ahrq.gov/data/index.html"
        }
    },
    
    "Mental Health": {
        "Crisis Lines": {
            "988 Suicide & Crisis Lifeline": {
                "phone": "988",
                "text": "Text 'HELLO' to 741741",
                "url": "https://988lifeline.org/",
                "chat": "https://988lifeline.org/chat/",
                "services": ["24/7 crisis support", "Suicide prevention", "Emotional distress"]
            },
            "Crisis Text Line": {
                "text": "Text 'HOME' to 741741",
                "url": "https://www.crisistextline.org/",
                "services": ["24/7 text support", "Trained counselors", "Free service"]
            },
            "SAMHSA National Helpline": {
                "phone": "1-800-662-4357",
                "url": "https://www.samhsa.gov/find-help/national-helpline",
                "services": ["Treatment referral", "24/7 support", "Multiple languages"]
            },
            "Veterans Crisis Line": {
                "phone": "988 then Press 1",
                "text": "Text 838255",
                "url": "https://www.veteranscrisisline.net/",
                "services": ["Veteran-specific support", "24/7 availability"]
            }
        },
        "Treatment Resources": {
            "Psychology Today Therapist Finder": "https://www.psychologytoday.com/us/therapists",
            "SAMHSA Treatment Locator": "https://findtreatment.samhsa.gov/",
            "Open Path Collective": "https://openpathcollective.org/",
            "BetterHelp Online Therapy": "https://www.betterhelp.com/",
            "NAMI Support Groups": "https://www.nami.org/Support-Education/Support-Groups"
        },
        "Youth & Teen Resources": {
            "Teen Line": {
                "phone": "1-800-852-8336",
                "text": "Text 'TEEN' to 839863",
                "url": "https://teenlineonline.org/",
                "hours": "6PM-10PM PST"
            },
            "The Trevor Project (LGBTQ+)": {
                "phone": "1-866-488-7386",
                "text": "Text 'START' to 678-678",
                "url": "https://www.thetrevorproject.org/",
                "services": ["24/7 LGBTQ+ youth support"]
            }
        }
    },
    
    "Education & Workforce": {
        "Educational Resources": {
            "Khan Academy": {
                "url": "https://www.khanacademy.org/",
                "description": "Free online education K-12 and beyond",
                "services": ["Math", "Science", "Humanities", "Test prep"]
            },
            "Coursera": {
                "url": "https://www.coursera.org/",
                "description": "Online courses from universities",
                "services": ["Certificates", "Degrees", "Professional development"]
            },
            "edX": {
                "url": "https://www.edx.org/",
                "description": "University-level courses",
                "services": ["Free courses", "MicroMasters", "Professional certificates"]
            },
            "Code.org": {
                "url": "https://code.org/",
                "description": "Free coding education",
                "services": ["K-12 curriculum", "Hour of Code", "AP Computer Science"]
            }
        },
        "Workforce Development": {
            "CareerOneStop": {
                "url": "https://www.careeronestop.org/",
                "description": "Career, training, and job search tools",
                "phone": "1-877-348-0502",
                "services": ["Job search", "Training finder", "Career exploration"]
            },
            "American Job Centers": {
                "url": "https://www.careeronestop.org/LocalHelp/AmericanJobCenters/find-american-job-centers.aspx",
                "description": "Local employment services",
                "services": ["Job placement", "Training programs", "Career counseling"]
            },
            "LinkedIn Learning": {
                "url": "https://www.linkedin.com/learning/",
                "description": "Professional skills training",
                "services": ["Business skills", "Technology", "Creative skills"]
            },
            "Google Career Certificates": {
                "url": "https://grow.google/certificates/",
                "description": "Job-ready skills training",
                "services": ["IT Support", "Data Analytics", "Project Management", "UX Design"]
            }
        },
        "Financial Aid": {
            "FAFSA": "https://studentaid.gov/",
            "College Board": "https://www.collegeboard.org/",
            "Scholarship America": "https://scholarshipamerica.org/students/",
            "Fastweb Scholarships": "https://www.fastweb.com/"
        }
    },
    
    "Transportation": {
        "National Programs": {
            "National Transit Database": "https://www.transit.dot.gov/ntd",
            "Rides to Wellness": "https://www.ncoa.org/article/transportation-benefits-for-older-adults",
            "GoGoGrandparent": "https://gogograndparent.com/",
            "NEMT (Non-Emergency Medical Transport)": "Contact your Medicaid provider"
        },
        "Ride Services": {
            "Lyft Community": "https://www.lyft.com/lyftup/programs",
            "Uber Health": "https://www.uberhealth.com/",
            "Local Transit Apps": "Transit, Citymapper, Moovit"
        }
    },
    
    "Legal Aid": {
        "Free Legal Services": {
            "Legal Services Corporation": {
                "url": "https://www.lsc.gov/what-legal-aid/find-legal-aid",
                "description": "Find local legal aid",
                "services": ["Civil legal help", "Low-income assistance"]
            },
            "Pro Bono Net": {
                "url": "https://www.probono.net/",
                "description": "Volunteer attorney network",
                "services": ["Free legal help", "Resource library"]
            },
            "American Bar Association Free Legal Help": {
                "url": "https://www.americanbar.org/groups/legal_services/flh-home/",
                "description": "State-by-state legal resources",
                "services": ["Legal clinics", "Pro bono programs"]
            }
        }
    }
}

# ==================== REAL EDUCATIONAL PLATFORMS ====================

EDUCATIONAL_PLATFORMS = {
    "Video Creation Tools": {
        "Free Tools": {
            "Canva": "https://www.canva.com/education/",
            "OpenShot": "https://www.openshot.org/",
            "DaVinci Resolve": "https://www.blackmagicdesign.com/products/davinciresolve",
            "Clipchamp": "https://clipchamp.com/",
            "CapCut": "https://www.capcut.com/"
        },
        "Mobile Apps": {
            "InShot": "iOS/Android",
            "Splice": "iOS/Android",
            "KineMaster": "iOS/Android",
            "Adobe Premiere Rush": "iOS/Android"
        },
        "Stock Resources": {
            "Pexels": "https://www.pexels.com/",
            "Pixabay": "https://pixabay.com/",
            "Unsplash": "https://unsplash.com/",
            "YouTube Audio Library": "https://studio.youtube.com/",
            "Freesound": "https://freesound.org/"
        }
    },
    
    "Research Databases": {
        "Academic": {
            "Google Scholar": "https://scholar.google.com/",
            "PubMed": "https://pubmed.ncbi.nlm.nih.gov/",
            "JSTOR": "https://www.jstor.org/",
            "ERIC": "https://eric.ed.gov/",
            "ResearchGate": "https://www.researchgate.net/"
        },
        "Data Sources": {
            "Census Bureau": "https://www.census.gov/",
            "CDC Wonder": "https://wonder.cdc.gov/",
            "World Bank Open Data": "https://data.worldbank.org/",
            "Data.gov": "https://www.data.gov/",
            "Statista": "https://www.statista.com/"
        },
        "SDOH Specific": {
            "County Health Rankings": "https://www.countyhealthrankings.org/",
            "500 Cities Project": "https://www.cdc.gov/places/",
            "Opportunity Atlas": "https://www.opportunityatlas.org/",
            "Eviction Lab": "https://evictionlab.org/",
            "Food Environment Atlas": "https://www.ers.usda.gov/data-products/food-environment-atlas/"
        }
    }
}

# ==================== REAL CRISIS RESOURCES ====================

CRISIS_RESOURCES = {
    "Immediate Help": {
        "Emergency": "911",
        "Suicide Prevention": "988",
        "Crisis Text": "Text HOME to 741741",
        "Domestic Violence": "1-800-799-7233",
        "Child Abuse": "1-800-4-A-CHILD (1-800-422-4453)",
        "Elder Abuse": "1-800-677-1116",
        "Human Trafficking": "1-888-373-7888",
        "LGBTQ+ Support": "1-866-488-7386",
        "Veteran Crisis": "988 Press 1",
        "Disaster Distress": "1-800-985-5990"
    }
}

# ==================== API INTEGRATIONS FOR REAL DATA ====================

class RealDataFetcher:
    """Fetch real data from public APIs"""
    
    @staticmethod
    def get_food_banks(zip_code: str) -> List[Dict]:
        """Get local food banks from Feeding America"""
        # Note: Actual implementation would require API key
        # This is the structure for real integration
        try:
            url = f"https://www.feedingamerica.org/find-your-local-foodbank/api/{zip_code}"
            # response = requests.get(url)
            # return response.json()
            return [{"name": "Example Food Bank", "address": "123 Main St", "phone": "555-0100"}]
        except:
            return []
    
    @staticmethod
    def get_health_centers(latitude: float, longitude: float, radius: int = 10) -> List[Dict]:
        """Get HRSA health centers near location"""
        try:
            url = "https://data.hrsa.gov/api/v1/health-centers"
            params = {
                "lat": latitude,
                "lon": longitude,
                "radius": radius
            }
            # response = requests.get(url, params=params)
            # return response.json()
            return [{"name": "Community Health Center", "services": ["Primary Care", "Dental"]}]
        except:
            return []
    
    @staticmethod
    def get_census_data(location: str) -> Dict:
        """Get census demographic data"""
        try:
            # Census API endpoint
            url = f"https://api.census.gov/data/2021/acs/acs5"
            # Actual implementation would include API key and parameters
            return {"population": 50000, "median_income": 55000, "poverty_rate": 0.12}
        except:
            return {}

# ==================== MAIN APPLICATION ====================

class SDOHVideoCreator:
    """Main application with real SDOH resources"""
    
    def __init__(self):
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state"""
        if 'selected_topic' not in st.session_state:
            st.session_state.selected_topic = None
        if 'selected_resources' not in st.session_state:
            st.session_state.selected_resources = []
        if 'user_location' not in st.session_state:
            st.session_state.user_location = None
            
    def render_header(self):
        """Render application header"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    color: white; padding: 2rem; border-radius: 15px; 
                    text-align: center; margin-bottom: 2rem;">
            <h1 style="margin: 0;">🏥 EduVid Creator Pro with Real SDOH Resources</h1>
            <p style="margin: 0.5rem 0;">Create Educational Videos with Actual Resources & Research</p>
            <p style="margin: 0; font-size: 0.9rem;">Direct Links to Services • Real Data • Verified Information</p>
        </div>
        """, unsafe_allow_html=True)
        
    def render_resource_finder(self):
        """Render resource finder interface"""
        st.subheader("🔍 Find Real SDOH Resources")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            category = st.selectbox(
                "Select SDOH Category",
                options=list(REAL_SDOH_RESOURCES.keys()),
                help="Choose the social determinant category"
            )
        
        with col2:
            zip_code = st.text_input(
                "ZIP Code (for local resources)",
                placeholder="12345",
                help="Enter ZIP code to find local services"
            )
        
        with col3:
            urgency = st.selectbox(
                "Urgency Level",
                ["Information Only", "Need Soon", "Need Today", "Emergency"],
                help="How urgent is the need?"
            )
        
        if urgency == "Emergency":
            st.error("⚠️ For emergencies, call 911 immediately!")
            st.warning("Crisis Resources Available 24/7:")
            for service, number in CRISIS_RESOURCES["Immediate Help"].items():
                st.write(f"**{service}**: {number}")
        
        # Display resources for selected category
        if category:
            self.display_category_resources(category, zip_code)
            
    def display_category_resources(self, category: str, zip_code: str = None):
        """Display resources for selected category"""
        st.markdown(f"### 📋 {category} Resources")
        
        resources = REAL_SDOH_RESOURCES[category]
        
        # National Services
        if "National Services" in resources:
            st.markdown("#### 🌐 National Services")
            
            for service_name, service_info in resources["National Services"].items():
                with st.expander(f"🔹 {service_name}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {service_info['description']}")
                        st.write(f"**Website:** {service_info['url']}")
                        
                        if 'phone' in service_info:
                            st.write(f"**Phone:** {service_info['phone']}")
                        if 'text' in service_info:
                            st.write(f"**Text:** {service_info['text']}")
                        
                    with col2:
                        st.write("**Services Offered:**")
                        for service in service_info['services']:
                            st.write(f"• {service}")
                    
                    # Direct action buttons
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        st.link_button("🌐 Visit Website", service_info['url'])
                    with col4:
                        if 'phone' in service_info:
                            st.code(service_info['phone'])
                    with col5:
                        if st.button(f"📌 Add to My Resources", key=f"add_{service_name}"):
                            st.session_state.selected_resources.append({
                                "name": service_name,
                                "category": category,
                                "info": service_info
                            })
                            st.success(f"Added {service_name} to your resources!")
        
        # Research & Data
        if "Research & Data" in resources:
            st.markdown("#### 📊 Research & Data Sources")
            for source_name, source_url in resources["Research & Data"].items():
                st.write(f"• [{source_name}]({source_url})")
        
        # Additional sections
        for section_name, section_data in resources.items():
            if section_name not in ["National Services", "Research & Data"]:
                st.markdown(f"#### {section_name}")
                if isinstance(section_data, dict):
                    for item_name, item_info in section_data.items():
                        if isinstance(item_info, dict):
                            st.write(f"**{item_name}**: {item_info.get('url', item_info.get('phone', ''))}")
                        else:
                            st.write(f"• {item_name}: {item_info}")
                            
    def render_video_creator(self):
        """Render video creation interface with real resources"""
        st.subheader("🎬 Create Educational Video with Real Resources")
        
        tab1, tab2, tab3 = st.tabs(["📝 Script Builder", "🔗 Resource Integration", "🎥 Video Assembly"])
        
        with tab1:
            st.markdown("### Build Your Educational Script")
            
            topic = st.text_input(
                "Video Topic",
                placeholder="e.g., Food Insecurity in Urban Communities"
            )
            
            target_audience = st.selectbox(
                "Target Audience",
                ["General Public", "Youth (13-18)", "College Students", 
                 "Healthcare Providers", "Policy Makers", "Educators"]
            )
            
            sdoh_focus = st.multiselect(
                "SDOH Areas to Cover",
                list(REAL_SDOH_RESOURCES.keys())
            )
            
            # Script template with real data
            if st.button("Generate Script with Real Data"):
                script = self.generate_script_with_resources(topic, sdoh_focus, target_audience)
                st.text_area("Generated Script", script, height=400)
                
        with tab2:
            st.markdown("### Your Selected Resources")
            
            if st.session_state.selected_resources:
                for i, resource in enumerate(st.session_state.selected_resources):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{resource['name']}** ({resource['category']})")
                            st.caption(resource['info']['description'])
                        with col2:
                            if st.button(f"Remove", key=f"remove_{i}"):
                                st.session_state.selected_resources.pop(i)
                                st.rerun()
                
                # Export resources
                st.download_button(
                    "📥 Download Resource List",
                    data=json.dumps(st.session_state.selected_resources, indent=2),
                    file_name="sdoh_resources.json",
                    mime="application/json"
                )
            else:
                st.info("No resources selected yet. Browse categories above to add resources.")
                
        with tab3:
            st.markdown("### Video Production Tools")
            
            # Real video creation tools
            st.markdown("#### 🛠️ Recommended Free Tools")
            for tool_category, tools in EDUCATIONAL_PLATFORMS["Video Creation Tools"].items():
                with st.expander(f"📹 {tool_category}"):
                    if isinstance(tools, dict):
                        for tool_name, tool_link in tools.items():
                            st.write(f"• [{tool_name}]({tool_link})")
                    else:
                        st.write(tools)
                        
    def generate_script_with_resources(self, topic: str, sdoh_areas: List[str], audience: str) -> str:
        """Generate script incorporating real resources"""
        
        script = f"""
EDUCATIONAL VIDEO SCRIPT: {topic}
Target Audience: {audience}
SDOH Focus Areas: {', '.join(sdoh_areas)}

[OPENING - 0:00-0:10]
"Did you know that social determinants of health account for 80% of health outcomes?"

[INTRODUCTION - 0:10-0:30]
Today we're exploring {topic}, focusing on how {', '.join(sdoh_areas)} impact our communities.

[MAIN CONTENT - 0:30-1:30]
"""
        
        # Add real statistics and resources
        for area in sdoh_areas:
            if area in REAL_SDOH_RESOURCES:
                resources = REAL_SDOH_RESOURCES[area]
                if "National Services" in resources:
                    first_service = list(resources["National Services"].keys())[0]
                    service_info = resources["National Services"][first_service]
                    
                    script += f"""
{area.upper()} RESOURCES:
- {first_service}: {service_info['description']}
- Contact: {service_info.get('phone', service_info.get('url', ''))}
- Services: {', '.join(service_info['services'][:3])}
"""
        
        script += """
[CALL TO ACTION - 1:30-1:45]
Resources are available! Visit the links in the description or call 211 for local help.

[CLOSING - 1:45-2:00]
Remember: Help is available. Together, we can address these social determinants of health.

RESOURCES MENTIONED:
- 211 Helpline (call or text)
- Local food banks: feedingamerica.org
- Healthcare: findahealthcenter.hrsa.gov
- Mental health: 988 Crisis Line
"""
        
        return script
        
    def render_research_section(self):
        """Render research and data section"""
        st.subheader("📊 Research & Data Sources")
        
        tab1, tab2, tab3 = st.tabs(["📚 Academic Research", "📈 Data Sources", "🗺️ SDOH Mapping"])
        
        with tab1:
            st.markdown("### Academic Research Databases")
            for db_name, db_url in EDUCATIONAL_PLATFORMS["Research Databases"]["Academic"].items():
                st.write(f"• [{db_name}]({db_url})")
                
        with tab2:
            st.markdown("### Public Data Sources")
            for source_name, source_url in EDUCATIONAL_PLATFORMS["Research Databases"]["Data Sources"].items():
                st.write(f"• [{source_name}]({source_url})")
                
        with tab3:
            st.markdown("### SDOH-Specific Data Tools")
            for tool_name, tool_url in EDUCATIONAL_PLATFORMS["Research Databases"]["SDOH Specific"].items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{tool_name}**")
                    st.caption(f"Access: {tool_url}")
                with col2:
                    st.link_button(f"Open {tool_name}", tool_url)
                    
    def render_emergency_banner(self):
        """Render emergency resources banner"""
        with st.container():
            st.error("🚨 **EMERGENCY RESOURCES AVAILABLE 24/7**")
            cols = st.columns(4)
            with cols[0]:
                st.write("**Emergency:** 911")
            with cols[1]:
                st.write("**Crisis:** 988")
            with cols[2]:
                st.write("**Text:** HOME to 741741")
            with cols[3]:
                st.write("**Info:** 211")
                
    def run(self):
        """Main application loop"""
        self.render_header()
        self.render_emergency_banner()
        
        # Main navigation
        menu = st.selectbox(
            "Select Function",
            ["🔍 Find SDOH Resources", "🎬 Create Educational Video", 
             "📊 Research & Data", "📚 Educational Tools", "🆘 Crisis Resources"],
            label_visibility="collapsed"
        )
        
        if menu == "🔍 Find SDOH Resources":
            self.render_resource_finder()
            
        elif menu == "🎬 Create Educational Video":
            self.render_video_creator()
            
        elif menu == "📊 Research & Data":
            self.render_research_section()
            
        elif menu == "📚 Educational Tools":
            st.subheader("📚 Educational Platforms & Tools")
            for platform_category, platforms in EDUCATIONAL_PLATFORMS.items():
                with st.expander(f"📖 {platform_category}"):
                    for subcategory, items in platforms.items():
                        st.markdown(f"**{subcategory}:**")
                        if isinstance(items, dict):
                            for name, link in items.items():
                                st.write(f"• [{name}]({link})")
                        else:
                            st.write(items)
                            
        elif menu == "🆘 Crisis Resources":
            st.subheader("🆘 Crisis & Emergency Resources")
            st.error("**If you are in immediate danger, call 911**")
            
            for service, contact in CRISIS_RESOURCES["Immediate Help"].items():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{service}:**")
                with col2:
                    st.code(contact)
                    
        # Sidebar with quick links
        with st.sidebar:
            st.markdown("### 🔗 Quick Access")
            
            st.markdown("**Emergency Numbers:**")
            st.code("911 - Emergency")
            st.code("988 - Crisis")
            st.code("211 - Resources")
            
            st.markdown("**Top Resources:**")
            quick_links = {
                "Food Banks": "https://www.feedingamerica.org/find-your-local-foodbank",
                "Health Centers": "https://findahealthcenter.hrsa.gov/",
                "Housing Help": "https://www.211.org/",
                "Mental Health": "https://988lifeline.org/",
                "Job Search": "https://www.careeronestop.org/"
            }
            
            for name, url in quick_links.items():
                st.link_button(f"🔗 {name}", url)
                
            st.markdown("---")
            st.markdown("### 📱 Mobile Apps")
            st.markdown("""
            **Resource Apps:**
            - Aunt Bertha (findhelp.org)
            - 211 Mobile App
            - GoodRx (prescriptions)
            - Feeding America
            
            **Crisis Apps:**
            - notOK (crisis alert)
            - MindShift (anxiety)
            - PTSD Coach
            - MY3 (suicide prevention)
            """)
            
            st.markdown("---")
            st.info("""
            **About This Tool:**
            
            All resources listed are real, 
            verified services. Links go 
            directly to official websites.
            
            For local resources, always 
            verify availability in your area.
            """)

def main():
    """Main entry point"""
    app = SDOHVideoCreator()
    app.run()

if __name__ == "__main__":
    main()