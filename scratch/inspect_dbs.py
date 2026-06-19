import json

vrm_path = "/Users/chandu/Downloads/emotion-agent/frontend/public/models/rem.vrm"
with open(vrm_path, "rb") as f:
    # Read glTF JSON header (it's a GLB file, so we parse the GLB format)
    header = f.read(12)
    magic, version, length = int.from_bytes(header[0:4], "little"), int.from_bytes(header[4:8], "little"), int.from_bytes(header[8:12], "little")
    print(f"GLB Magic: {magic:#x}, Version: {version}, Length: {length}")
    
    # Read chunk 0 (JSON)
    chunk_header = f.read(8)
    chunk_length = int.from_bytes(chunk_header[0:4], "little")
    chunk_type = int.from_bytes(chunk_header[4:8], "little")
    print(f"Chunk 0 Length: {chunk_length}, Type: {chunk_type:#x}")
    
    json_bytes = f.read(chunk_length)
    gltf = json.loads(json_bytes.decode("utf-8"))

# Find nodes and check their translations
nodes = gltf.get("nodes", [])

# VRM 0.0 humanoid bones are mapped in extensions.VRM.humanoid.humanBones
extensions = gltf.get("extensions", {})
vrm_ext = extensions.get("VRM", {})
humanoid = vrm_ext.get("humanoid", {})
human_bones = humanoid.get("humanBones", [])

bone_node_indices = {}
for bone in human_bones:
    bone_node_indices[bone.get("bone")] = bone.get("node")

print("Humanoid Bone Node Indices:")
print(json.dumps(bone_node_indices, indent=2))

print("\nBone Translations (Child relative to Parent):")
bones_to_check = [
    ("leftUpperArm", "leftLowerArm"),
    ("leftLowerArm", "leftHand"),
    ("rightUpperArm", "rightLowerArm"),
    ("rightLowerArm", "rightHand")
]

for parent_name, child_name in bones_to_check:
    parent_idx = bone_node_indices.get(parent_name)
    child_idx = bone_node_indices.get(child_name)
    if parent_idx is not None and child_idx is not None:
        parent_node = nodes[parent_idx]
        child_node = nodes[child_idx]
        print(f"\nParent: {parent_name} (Node {parent_idx}, Name: {parent_node.get('name')})")
        print(f"Child: {child_name} (Node {child_idx}, Name: {child_node.get('name')})")
        print(f"Child Translation: {child_node.get('translation')}")
