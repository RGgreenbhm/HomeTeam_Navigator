"""Prompt Manager for AutoScribe - handles prompt loading, storage, and Azure sync.

Manages system prompts (admin-controlled) and user custom prompts.
Syncs with Azure Blob Storage for cross-device access.
"""

import os
import json
import logging
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Standard prompt types."""
    SBAR = "sbar"
    OFFICE_NOTE = "office_note"
    VIDEO_NOTE = "video_note"
    CUSTOM = "custom"


@dataclass
class PromptTemplate:
    """A prompt template for medical note generation."""
    id: str
    name: str
    prompt_type: PromptType
    content: str
    author: str  # "system" for admin prompts, user_id for custom
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "prompt_type": self.prompt_type.value,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            prompt_type=PromptType(data["prompt_type"]),
            content=data["content"],
            author=data["author"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            description=data.get("description"),
        )


class PromptManager:
    """Manages prompt templates for AutoScribe.

    Handles:
    - Loading system prompts from local files
    - Managing user custom prompts
    - Syncing with Azure Blob Storage
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt files.
                        Defaults to app/autoscribe/prompts/
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "prompts"

        self.prompts_dir = prompts_dir
        self.system_dir = prompts_dir / "system"
        self.custom_dir = prompts_dir / "custom"

        # Ensure directories exist
        self.system_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir.mkdir(parents=True, exist_ok=True)

        # Cache loaded prompts
        self._system_prompts: Dict[str, PromptTemplate] = {}
        self._custom_prompts: Dict[str, Dict[str, PromptTemplate]] = {}  # user_id -> prompts

        # Load system prompts on init
        self._load_system_prompts()

    def _load_system_prompts(self) -> None:
        """Load all system prompts from the system directory."""
        prompt_files = {
            "sbar.md": (PromptType.SBAR, "SBAR", "SBAR format for situation, background, assessment, recommendations"),
            "office_note.md": (PromptType.OFFICE_NOTE, "Office Note", "Standard office visit note format"),
            "video_note.md": (PromptType.VIDEO_NOTE, "Video Note", "Video/telehealth visit note format"),
        }

        for filename, (prompt_type, name, description) in prompt_files.items():
            filepath = self.system_dir / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding="utf-8")
                    now = datetime.now()

                    # Get file modification time
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)

                    self._system_prompts[prompt_type.value] = PromptTemplate(
                        id=prompt_type.value,
                        name=name,
                        prompt_type=prompt_type,
                        content=content,
                        author="system",
                        created_at=mtime,
                        updated_at=mtime,
                        description=description,
                    )
                    logger.info(f"Loaded system prompt: {name}")
                except Exception as e:
                    logger.error(f"Failed to load prompt {filename}: {e}")

    def get_system_prompt(self, prompt_type: PromptType) -> Optional[PromptTemplate]:
        """Get a system prompt by type.

        Args:
            prompt_type: The type of prompt to retrieve

        Returns:
            PromptTemplate if found, None otherwise
        """
        return self._system_prompts.get(prompt_type.value)

    def get_all_system_prompts(self) -> List[PromptTemplate]:
        """Get all system prompts.

        Returns:
            List of all system prompt templates
        """
        return list(self._system_prompts.values())

    def get_user_prompts(self, user_id: str) -> List[PromptTemplate]:
        """Get all custom prompts for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of user's custom prompts
        """
        self._load_user_prompts(user_id)
        return list(self._custom_prompts.get(user_id, {}).values())

    def _load_user_prompts(self, user_id: str) -> None:
        """Load custom prompts for a user from disk."""
        user_dir = self.custom_dir / user_id
        if not user_dir.exists():
            self._custom_prompts[user_id] = {}
            return

        self._custom_prompts[user_id] = {}

        # Load from registry file if exists
        registry_file = user_dir / "registry.json"
        if registry_file.exists():
            try:
                registry = json.loads(registry_file.read_text(encoding="utf-8"))
                for prompt_data in registry.get("prompts", []):
                    prompt = PromptTemplate.from_dict(prompt_data)
                    self._custom_prompts[user_id][prompt.id] = prompt
            except Exception as e:
                logger.error(f"Failed to load user prompts registry: {e}")

    def save_user_prompt(
        self,
        user_id: str,
        name: str,
        content: str,
        description: Optional[str] = None,
        prompt_id: Optional[str] = None,
    ) -> PromptTemplate:
        """Save a custom prompt for a user.

        Args:
            user_id: The user's ID
            name: Display name for the prompt
            content: The prompt content
            description: Optional description
            prompt_id: Optional ID for updating existing prompt

        Returns:
            The saved PromptTemplate
        """
        user_dir = self.custom_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()

        if prompt_id and user_id in self._custom_prompts and prompt_id in self._custom_prompts[user_id]:
            # Update existing
            prompt = self._custom_prompts[user_id][prompt_id]
            prompt.name = name
            prompt.content = content
            prompt.description = description
            prompt.updated_at = now
        else:
            # Create new
            import uuid
            prompt_id = prompt_id or str(uuid.uuid4())[:8]
            prompt = PromptTemplate(
                id=prompt_id,
                name=name,
                prompt_type=PromptType.CUSTOM,
                content=content,
                author=user_id,
                created_at=now,
                updated_at=now,
                description=description,
            )

        # Update cache
        if user_id not in self._custom_prompts:
            self._custom_prompts[user_id] = {}
        self._custom_prompts[user_id][prompt.id] = prompt

        # Save to disk
        self._save_user_registry(user_id)

        logger.info(f"Saved custom prompt '{name}' for user {user_id}")
        return prompt

    def _save_user_registry(self, user_id: str) -> None:
        """Save user's prompts registry to disk."""
        user_dir = self.custom_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        registry = {
            "user_id": user_id,
            "updated_at": datetime.now().isoformat(),
            "prompts": [p.to_dict() for p in self._custom_prompts.get(user_id, {}).values()],
        }

        registry_file = user_dir / "registry.json"
        registry_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    def delete_user_prompt(self, user_id: str, prompt_id: str) -> bool:
        """Delete a custom prompt.

        Args:
            user_id: The user's ID
            prompt_id: The prompt ID to delete

        Returns:
            True if deleted, False if not found
        """
        if user_id in self._custom_prompts and prompt_id in self._custom_prompts[user_id]:
            del self._custom_prompts[user_id][prompt_id]
            self._save_user_registry(user_id)
            logger.info(f"Deleted custom prompt {prompt_id} for user {user_id}")
            return True
        return False

    def get_prompt_for_generation(self, prompt_type: PromptType, user_id: Optional[str] = None, custom_prompt_id: Optional[str] = None) -> Optional[str]:
        """Get the prompt content for note generation.

        Args:
            prompt_type: Type of prompt (SBAR, OFFICE_NOTE, VIDEO_NOTE, CUSTOM)
            user_id: User ID (required for custom prompts)
            custom_prompt_id: ID of custom prompt (required if prompt_type is CUSTOM)

        Returns:
            Prompt content string, or None if not found
        """
        if prompt_type == PromptType.CUSTOM:
            if not user_id or not custom_prompt_id:
                logger.error("user_id and custom_prompt_id required for custom prompts")
                return None

            self._load_user_prompts(user_id)
            prompt = self._custom_prompts.get(user_id, {}).get(custom_prompt_id)
            return prompt.content if prompt else None
        else:
            prompt = self.get_system_prompt(prompt_type)
            return prompt.content if prompt else None

    def reload_system_prompts(self) -> None:
        """Reload system prompts from disk (e.g., after Azure sync)."""
        self._system_prompts.clear()
        self._load_system_prompts()
        logger.info("Reloaded system prompts from disk")


# Singleton instance for easy access
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get the singleton PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
