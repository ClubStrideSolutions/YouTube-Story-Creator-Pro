"""
Data storage module for saving generated content with embeddings
"""

import os
import json
import pickle
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import numpy as np
from PIL import Image
import streamlit as st

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import MongoDB for database storage
try:
    import pymongo
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


class ContentStorage:
    """Manages storage of generated content with embeddings."""
    
    def __init__(self, storage_dir: str = "generated_content"):
        """Initialize content storage."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.images_dir = self.storage_dir / "images"
        self.videos_dir = self.storage_dir / "videos"
        self.scripts_dir = self.storage_dir / "scripts"
        self.embeddings_dir = self.storage_dir / "embeddings"
        self.metadata_dir = self.storage_dir / "metadata"
        
        for dir_path in [self.images_dir, self.videos_dir, self.scripts_dir, 
                         self.embeddings_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Initialize OpenAI client for embeddings if available
        if OPENAI_AVAILABLE:
            from config import OPENAI_API_KEY
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        else:
            self.openai_client = None
        
        # Initialize MongoDB if available
        if MONGODB_AVAILABLE:
            from config import MONGODB_URI
            if MONGODB_URI:
                try:
                    self.mongo_client = MongoClient(MONGODB_URI)
                    self.db = self.mongo_client.youtube_creator
                    self.content_collection = self.db.generated_content
                    self.mongodb_connected = True
                except Exception as e:
                    st.warning(f"MongoDB connection failed: {e}")
                    self.mongodb_connected = False
            else:
                self.mongodb_connected = False
        else:
            self.mongodb_connected = False
    
    def generate_content_id(self, user_id: str, timestamp: datetime) -> str:
        """Generate unique content ID."""
        id_string = f"{user_id}_{timestamp.isoformat()}"
        return hashlib.md5(id_string.encode()).hexdigest()[:12]
    
    def save_content(
        self,
        user_id: str,
        story: Dict,
        images: List[Image.Image],
        video_path: Optional[str],
        audio_bytes: Optional[bytes],
        settings: Dict,
        template: str
    ) -> Dict:
        """Save all generated content with organization."""
        
        # Generate unique content ID
        timestamp = datetime.now()
        content_id = self.generate_content_id(user_id, timestamp)
        
        # Create content directory
        content_dir = self.storage_dir / content_id
        content_dir.mkdir(exist_ok=True)
        
        # Save images
        image_paths = self._save_images(images, content_id)
        
        # Save video
        video_saved_path = self._save_video(video_path, content_id)
        
        # Save script
        script_path = self._save_script(story, content_id)
        
        # Generate and save embeddings
        embeddings = self._generate_embeddings(story)
        embeddings_path = self._save_embeddings(embeddings, content_id)
        
        # Save audio
        audio_path = None
        if audio_bytes:
            audio_path = self._save_audio(audio_bytes, content_id)
        
        # Create metadata
        metadata = {
            "content_id": content_id,
            "user_id": user_id,
            "timestamp": timestamp.isoformat(),
            "story": story,
            "template": template,
            "settings": settings,
            "file_paths": {
                "images": image_paths,
                "video": video_saved_path,
                "audio": audio_path,
                "script": script_path,
                "embeddings": embeddings_path
            },
            "stats": {
                "duration": settings.get("duration", 30),
                "image_count": len(images),
                "has_captions": settings.get("captions", False),
                "has_music": settings.get("music", False),
                "quality": settings.get("quality", "high")
            }
        }
        
        # Save metadata
        metadata_path = self._save_metadata(metadata, content_id)
        
        # Store in MongoDB if available
        if self.mongodb_connected:
            self._store_in_mongodb(metadata, embeddings)
        
        # Update index
        self._update_index(content_id, metadata)
        
        st.success(f"✅ Content saved with ID: {content_id}")
        
        return {
            "content_id": content_id,
            "paths": metadata["file_paths"],
            "metadata": metadata
        }
    
    def _save_images(self, images: List[Image.Image], content_id: str) -> List[str]:
        """Save images to disk."""
        image_paths = []
        images_subdir = self.images_dir / content_id
        images_subdir.mkdir(exist_ok=True)
        
        for i, img in enumerate(images):
            image_path = images_subdir / f"scene_{i+1}.png"
            img.save(image_path, "PNG")
            image_paths.append(str(image_path))
        
        return image_paths
    
    def _save_video(self, video_path: Optional[str], content_id: str) -> Optional[str]:
        """Save video file."""
        if not video_path or not os.path.exists(video_path):
            return None
        
        import shutil
        video_filename = f"{content_id}_video.mp4"
        saved_path = self.videos_dir / video_filename
        shutil.copy2(video_path, saved_path)
        
        return str(saved_path)
    
    def _save_audio(self, audio_bytes: bytes, content_id: str) -> str:
        """Save audio file."""
        audio_filename = f"{content_id}_narration.mp3"
        audio_path = self.storage_dir / content_id / audio_filename
        
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        
        return str(audio_path)
    
    def _save_script(self, story: Dict, content_id: str) -> str:
        """Save story script as formatted text."""
        script_filename = f"{content_id}_script.txt"
        script_path = self.scripts_dir / script_filename
        
        # Format script content
        script_content = f"""
TITLE: {story.get('title', 'Untitled')}
GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
CONTENT ID: {content_id}

=====================================
STORY STRUCTURE
=====================================

HOOK:
{story.get('hook', '')}

PROBLEM:
{story.get('problem', '')}

SOLUTION:
{story.get('solution', '')}

IMPACT:
{story.get('impact', '')}

CALL TO ACTION:
{story.get('call_to_action', '')}

=====================================
VISUAL SCENES
=====================================

"""
        for i, scene in enumerate(story.get('scenes', []), 1):
            script_content += f"SCENE {i}:\n{scene}\n\n"
        
        script_content += """
=====================================
FULL NARRATION
=====================================

"""
        # Combine all text for narration
        narration_parts = [
            story.get('hook', ''),
            story.get('problem', ''),
            story.get('solution', ''),
            story.get('impact', ''),
            story.get('call_to_action', '')
        ]
        full_narration = ' '.join([part for part in narration_parts if part])
        script_content += full_narration
        
        # Save script
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Also save as JSON for programmatic access
        json_path = self.scripts_dir / f"{content_id}_script.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(story, f, indent=2, ensure_ascii=False)
        
        return str(script_path)
    
    def _generate_embeddings(self, story: Dict) -> Optional[Dict]:
        """Generate embeddings for the story content."""
        if not self.openai_client:
            return None
        
        try:
            # Combine all story text
            full_text = ' '.join([
                story.get('title', ''),
                story.get('hook', ''),
                story.get('problem', ''),
                story.get('solution', ''),
                story.get('impact', ''),
                story.get('call_to_action', ''),
                ' '.join(story.get('scenes', []))
            ])
            
            # Generate embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=full_text
            )
            
            embedding_vector = response.data[0].embedding
            
            # Also generate individual embeddings for each component
            component_embeddings = {}
            for key in ['title', 'hook', 'problem', 'solution', 'impact', 'call_to_action']:
                if story.get(key):
                    comp_response = self.openai_client.embeddings.create(
                        model="text-embedding-3-small",
                        input=story.get(key, '')
                    )
                    component_embeddings[key] = comp_response.data[0].embedding
            
            return {
                "full_embedding": embedding_vector,
                "component_embeddings": component_embeddings,
                "model": "text-embedding-3-small",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            st.warning(f"Could not generate embeddings: {e}")
            return None
    
    def _save_embeddings(self, embeddings: Optional[Dict], content_id: str) -> Optional[str]:
        """Save embeddings to disk."""
        if not embeddings:
            return None
        
        embeddings_filename = f"{content_id}_embeddings.pkl"
        embeddings_path = self.embeddings_dir / embeddings_filename
        
        with open(embeddings_path, 'wb') as f:
            pickle.dump(embeddings, f)
        
        # Also save as numpy arrays for easier loading
        np_path = self.embeddings_dir / f"{content_id}_embeddings.npz"
        np.savez_compressed(
            np_path,
            full_embedding=np.array(embeddings["full_embedding"]),
            metadata=json.dumps({
                "model": embeddings["model"],
                "timestamp": embeddings["timestamp"]
            })
        )
        
        return str(embeddings_path)
    
    def _save_metadata(self, metadata: Dict, content_id: str) -> str:
        """Save metadata to disk."""
        metadata_filename = f"{content_id}_metadata.json"
        metadata_path = self.metadata_dir / metadata_filename
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return str(metadata_path)
    
    def _store_in_mongodb(self, metadata: Dict, embeddings: Optional[Dict]):
        """Store content in MongoDB."""
        if not self.mongodb_connected:
            return
        
        try:
            # Prepare document
            doc = metadata.copy()
            
            # Add embeddings if available
            if embeddings:
                # Store embedding as list for MongoDB
                doc["embeddings"] = {
                    "full": embeddings["full_embedding"],
                    "model": embeddings["model"],
                    "generated_at": embeddings["timestamp"]
                }
            
            # Insert into MongoDB
            self.content_collection.insert_one(doc)
            
        except Exception as e:
            st.warning(f"Could not store in MongoDB: {e}")
    
    def _update_index(self, content_id: str, metadata: Dict):
        """Update the content index."""
        index_path = self.storage_dir / "content_index.json"
        
        # Load existing index
        if index_path.exists():
            with open(index_path, 'r') as f:
                index = json.load(f)
        else:
            index = {}
        
        # Add new entry
        index[content_id] = {
            "user_id": metadata["user_id"],
            "timestamp": metadata["timestamp"],
            "title": metadata["story"].get("title", "Untitled"),
            "template": metadata["template"],
            "duration": metadata["stats"]["duration"]
        }
        
        # Save updated index
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    def search_by_embedding(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar content using embeddings."""
        if not self.openai_client:
            return []
        
        try:
            # Generate query embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = np.array(response.data[0].embedding)
            
            # Load all embeddings
            results = []
            for embedding_file in self.embeddings_dir.glob("*_embeddings.npz"):
                data = np.load(embedding_file)
                stored_embedding = data["full_embedding"]
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, stored_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                )
                
                # Get content ID from filename
                content_id = embedding_file.stem.replace("_embeddings", "")
                
                results.append({
                    "content_id": content_id,
                    "similarity": float(similarity)
                })
            
            # Sort by similarity and return top k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            st.error(f"Search failed: {e}")
            return []
    
    def load_content(self, content_id: str) -> Optional[Dict]:
        """Load previously saved content."""
        metadata_path = self.metadata_dir / f"{content_id}_metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return metadata
    
    def list_user_content(self, user_id: str) -> List[Dict]:
        """List all content for a specific user."""
        user_content = []
        
        for metadata_file in self.metadata_dir.glob("*_metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            if metadata.get("user_id") == user_id:
                user_content.append({
                    "content_id": metadata["content_id"],
                    "title": metadata["story"].get("title", "Untitled"),
                    "timestamp": metadata["timestamp"],
                    "template": metadata["template"],
                    "duration": metadata["stats"]["duration"]
                })
        
        # Sort by timestamp (newest first)
        user_content.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return user_content
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        stats = {
            "total_content": len(list(self.metadata_dir.glob("*_metadata.json"))),
            "total_videos": len(list(self.videos_dir.glob("*.mp4"))),
            "total_images": len(list(self.images_dir.glob("**/*.png"))),
            "total_scripts": len(list(self.scripts_dir.glob("*.txt"))),
            "storage_size_mb": 0
        }
        
        # Calculate storage size
        for path in self.storage_dir.rglob("*"):
            if path.is_file():
                stats["storage_size_mb"] += path.stat().st_size / (1024 * 1024)
        
        stats["storage_size_mb"] = round(stats["storage_size_mb"], 2)
        
        return stats