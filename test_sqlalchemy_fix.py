"""
Quick test to verify SQLAlchemy metadata field fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_asset_model_import():
    """Test that Asset model can be imported without SQLAlchemy reserved name error"""
    try:
        from api.models import Asset
        print("✅ Successfully imported Asset model")
        
        # Test that we can create an instance
        asset = Asset(
            asset_tag="TEST001",
            item_type="Dumbbell",
            location="Test Room",
        )
        
        # Test metadata property
        asset.metadata = {"test": "value"}
        assert asset.metadata == {"test": "value"}
        assert asset.asset_metadata == {"test": "value"}
        
        print("✅ Asset model metadata property works correctly")
        print("✅ SQLAlchemy reserved name conflict resolved")
        return True
        
    except Exception as e:
        print(f"❌ Error importing Asset model: {e}")
        return False

if __name__ == "__main__":
    success = test_asset_model_import()
    if success:
        print("\n🎉 Fix verified! The SQLAlchemy reserved name issue has been resolved.")
    else:
        print("\n💥 Fix failed! There are still issues with the model.")