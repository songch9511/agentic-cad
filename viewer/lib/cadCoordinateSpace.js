export const CAD_TO_VIEWER_TRANSFORM = Object.freeze([
  1, 0, 0, 0,
  0, 0, 1, 0,
  0, -1, 0, 0,
  0, 0, 0, 1
]);

const IDENTITY_TRANSFORM = Object.freeze([
  1, 0, 0, 0,
  0, 1, 0, 0,
  0, 0, 1, 0,
  0, 0, 0, 1
]);

function toTransformArray(value, fallback = IDENTITY_TRANSFORM) {
  if (!Array.isArray(value) || value.length !== 16) {
    return [...fallback];
  }
  return value.map((component, index) => Number.isFinite(Number(component)) ? Number(component) : fallback[index]);
}

function toVector3(value, fallback = [0, 0, 0]) {
  if (!Array.isArray(value) && !(value instanceof Float32Array)) {
    return [...fallback];
  }
  return [
    Number.isFinite(Number(value[0])) ? Number(value[0]) : fallback[0],
    Number.isFinite(Number(value[1])) ? Number(value[1]) : fallback[1],
    Number.isFinite(Number(value[2])) ? Number(value[2]) : fallback[2]
  ];
}

export function multiplyTransforms(left, right) {
  const a = toTransformArray(left);
  const b = toTransformArray(right);
  const product = new Array(16).fill(0);
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 4; column += 1) {
      let total = 0;
      for (let offset = 0; offset < 4; offset += 1) {
        total += a[(row * 4) + offset] * b[(offset * 4) + column];
      }
      product[(row * 4) + column] = total;
    }
  }
  return product;
}

export function transformPoint(transform, point) {
  const matrix = toTransformArray(transform);
  const [x, y, z] = toVector3(point);
  return [
    (matrix[0] * x) + (matrix[1] * y) + (matrix[2] * z) + matrix[3],
    (matrix[4] * x) + (matrix[5] * y) + (matrix[6] * z) + matrix[7],
    (matrix[8] * x) + (matrix[9] * y) + (matrix[10] * z) + matrix[11]
  ];
}

export function transformVector(transform, vector) {
  const matrix = toTransformArray(transform);
  const [x, y, z] = toVector3(vector, [0, 0, 1]);
  const next = [
    (matrix[0] * x) + (matrix[1] * y) + (matrix[2] * z),
    (matrix[4] * x) + (matrix[5] * y) + (matrix[6] * z),
    (matrix[8] * x) + (matrix[9] * y) + (matrix[10] * z)
  ];
  const length = Math.hypot(next[0], next[1], next[2]) || 1;
  return [next[0] / length, next[1] / length, next[2] / length];
}

export function transformBounds(bounds, transform) {
  const min = Array.isArray(bounds?.min) ? bounds.min : [0, 0, 0];
  const max = Array.isArray(bounds?.max) ? bounds.max : [0, 0, 0];
  const corners = [
    [min[0], min[1], min[2]],
    [min[0], min[1], max[2]],
    [min[0], max[1], min[2]],
    [min[0], max[1], max[2]],
    [max[0], min[1], min[2]],
    [max[0], min[1], max[2]],
    [max[0], max[1], min[2]],
    [max[0], max[1], max[2]]
  ].map((corner) => transformPoint(transform, corner));
  const xs = corners.map((point) => point[0]);
  const ys = corners.map((point) => point[1]);
  const zs = corners.map((point) => point[2]);
  return {
    min: [Math.min(...xs), Math.min(...ys), Math.min(...zs)],
    max: [Math.max(...xs), Math.max(...ys), Math.max(...zs)]
  };
}

export function transformMeshData(meshData, transform) {
  if (!meshData?.vertices?.length) {
    return meshData;
  }
  const vertices = new Float32Array(meshData.vertices.length);
  for (let index = 0; index + 2 < meshData.vertices.length; index += 3) {
    const point = transformPoint(transform, [
      meshData.vertices[index],
      meshData.vertices[index + 1],
      meshData.vertices[index + 2]
    ]);
    vertices[index] = point[0];
    vertices[index + 1] = point[1];
    vertices[index + 2] = point[2];
  }

  const normals = meshData.normals?.length === meshData.vertices.length
    ? new Float32Array(meshData.normals.length)
    : meshData.normals;
  if (normals instanceof Float32Array && normals !== meshData.normals) {
    for (let index = 0; index + 2 < meshData.normals.length; index += 3) {
      const normal = transformVector(transform, [
        meshData.normals[index],
        meshData.normals[index + 1],
        meshData.normals[index + 2]
      ]);
      normals[index] = normal[0];
      normals[index + 1] = normal[1];
      normals[index + 2] = normal[2];
    }
  }

  const parts = Array.isArray(meshData.parts)
    ? meshData.parts.map((part) => ({
      ...part,
      bounds: part?.bounds ? transformBounds(part.bounds, transform) : part?.bounds
    }))
    : meshData.parts;

  return {
    ...meshData,
    vertices,
    normals,
    bounds: transformBounds(meshData.bounds, transform),
    parts,
    coordinateSpace: "viewer"
  };
}
