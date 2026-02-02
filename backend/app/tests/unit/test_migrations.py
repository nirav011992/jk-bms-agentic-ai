"""Unit tests for database migrations (Phase 2)."""
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command
import os


@pytest.mark.asyncio
async def test_alembic_configuration_exists():
    """Test that Alembic configuration file exists."""
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "../../../alembic.ini")
    assert os.path.exists(alembic_ini_path), "alembic.ini not found"


@pytest.mark.asyncio
async def test_alembic_migrations_directory_exists():
    """Test that migrations directory exists."""
    migrations_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    assert os.path.exists(migrations_dir), "alembic/versions directory not found"


@pytest.mark.asyncio
async def test_alembic_env_configuration():
    """Test that Alembic env.py is configured correctly."""
    env_path = os.path.join(os.path.dirname(__file__), "../../../alembic/env.py")
    assert os.path.exists(env_path), "alembic/env.py not found"

    # Read env.py and check for required imports
    with open(env_path, 'r') as f:
        content = f.read()
        assert "from app.db.session import Base" in content
        assert "from app.core.config import settings" in content
        assert "target_metadata = Base.metadata" in content


@pytest.mark.asyncio
async def test_initial_migration_exists():
    """Test that initial migration file exists."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and f != '__pycache__']
    assert len(migration_files) > 0, "No migration files found"


@pytest.mark.asyncio
async def test_migration_file_structure():
    """Test that migration files have correct structure."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]

    for migration_file in migration_files:
        file_path = os.path.join(versions_dir, migration_file)
        with open(file_path, 'r') as f:
            content = f.read()
            # Check for required functions
            assert "def upgrade()" in content, f"{migration_file} missing upgrade() function"
            assert "def downgrade()" in content, f"{migration_file} missing downgrade() function"


@pytest.mark.asyncio
async def test_migration_creates_all_tables():
    """Test that initial migration creates all required tables."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    initial_migration = os.path.join(versions_dir, "001_initial_migration.py")

    if os.path.exists(initial_migration):
        with open(initial_migration, 'r') as f:
            content = f.read()

            # Check for all required tables
            required_tables = ['users', 'books', 'reviews', 'documents', 'borrows']
            for table in required_tables:
                assert f"create_table('{table}" in content, f"Table '{table}' not created in migration"


@pytest.mark.asyncio
async def test_alembic_script_directory_valid():
    """Test that Alembic script directory is valid."""
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "../../../alembic.ini")

    try:
        alembic_cfg = Config(alembic_ini_path)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script is not None
    except Exception as e:
        pytest.fail(f"Failed to load Alembic configuration: {str(e)}")


@pytest.mark.asyncio
async def test_migration_revision_ids():
    """Test that migrations have proper revision IDs."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]

    for migration_file in migration_files:
        file_path = os.path.join(versions_dir, migration_file)
        with open(file_path, 'r') as f:
            content = f.read()
            # Check for revision identifiers
            assert "revision:" in content or "revision =" in content
            assert "down_revision:" in content or "down_revision =" in content


@pytest.mark.asyncio
async def test_models_match_migrations():
    """Test that current models match migration definitions."""
    # This is a basic check - full check would require running migrations
    from app.models import User, Book, Review, Document, Borrow

    # Check that models exist and have required attributes
    assert hasattr(User, '__tablename__')
    assert hasattr(Book, '__tablename__')
    assert hasattr(Review, '__tablename__')
    assert hasattr(Document, '__tablename__')
    assert hasattr(Borrow, '__tablename__')

    # Check table names
    assert User.__tablename__ == 'users'
    assert Book.__tablename__ == 'books'
    assert Review.__tablename__ == 'reviews'
    assert Document.__tablename__ == 'documents'
    assert Borrow.__tablename__ == 'borrows'


@pytest.mark.asyncio
async def test_borrow_status_enum_in_migration():
    """Test that BorrowStatus enum is created in migration."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    initial_migration = os.path.join(versions_dir, "001_initial_migration.py")

    if os.path.exists(initial_migration):
        with open(initial_migration, 'r') as f:
            content = f.read()
            # Check for enum creation
            assert "BorrowStatus" in content or "borrowstatus" in content.lower()
            assert "ACTIVE" in content
            assert "RETURNED" in content
            assert "OVERDUE" in content


@pytest.mark.asyncio
async def test_downgrade_removes_tables():
    """Test that downgrade removes all tables."""
    versions_dir = os.path.join(os.path.dirname(__file__), "../../../alembic/versions")
    initial_migration = os.path.join(versions_dir, "001_initial_migration.py")

    if os.path.exists(initial_migration):
        with open(initial_migration, 'r') as f:
            content = f.read()

            # Find downgrade function
            downgrade_start = content.find("def downgrade()")
            if downgrade_start != -1:
                downgrade_content = content[downgrade_start:]
                # Check that tables are dropped
                assert "drop_table" in downgrade_content.lower()
