import nibabel as nib
import numpy as np
from scipy.ndimage import affine_transform

# Load image
img = nib.load('CT_registered.nii')
data = img.get_fdata()
affine = img.affine

# Compute the transformation that maps from target space to original voxel space
# We want the new affine to be identity (or diagonal), so the transform is:
inv_affine = np.linalg.inv(affine)

# Output shape: same physical size but voxel-aligned
# Compute new shape by mapping corners
def get_bounding_box(shape, affine):
    corners = np.array(np.meshgrid(
        [0, shape[0] - 1],
        [0, shape[1] - 1],
        [0, shape[2] - 1],
        indexing='ij'
    )).reshape(3, -1)
    corners = np.vstack((corners, np.ones((1, corners.shape[1]))))  # make homogenous
    real_coords = affine @ corners
    mins = real_coords[:3].min(axis=1)
    maxs = real_coords[:3].max(axis=1)
    return mins, maxs

mins, maxs = get_bounding_box(data.shape, affine)

# Choose isotropic voxel size (or take from original)
voxel_size = np.linalg.norm(affine[:3, :3], axis=0)
new_shape = np.ceil((maxs - mins) / voxel_size).astype(int)

# Compute new affine (diagonal)
new_affine = np.eye(4)
new_affine[:3, :3] = np.diag(voxel_size)
new_affine[:3, 3] = mins

# Compute transform from new voxel space to old voxel space
# (we invert the mapping from voxel_new -> world -> voxel_old)
transform = np.linalg.inv(affine) @ new_affine

# Apply the transformation to resample
resampled_data = affine_transform(
    data,
    matrix=transform[:3, :3],
    offset=transform[:3, 3],
    output_shape=tuple(new_shape),
    order=1  # linear interpolation
)

# Save if needed
new_img = nib.Nifti1Image(resampled_data, new_affine)
nib.save(new_img, 'CT_resampled.nii')