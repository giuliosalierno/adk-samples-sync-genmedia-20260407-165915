#!/bin/bash
# Copy MediaPipe files to public directory for bundling

mkdir -p public/mediapipe/face_mesh
cp -r node_modules/@mediapipe/face_mesh/* public/mediapipe/face_mesh/
# Remove empty SIMD data file that causes loading errors
rm -f public/mediapipe/face_mesh/face_mesh_solution_simd_wasm_bin.data
echo "✅ MediaPipe files copied to public/mediapipe/face_mesh"
