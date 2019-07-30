function X = erode_or_dilate(X,type,conn,op_fact)
% type: type of operation: 'erode' or 'dilate'
% conn: connectivity, should be 6, 18 or 26 (default = 6)
% op_fact: number of iterations of the chosen operation (default = 1)

if strcmp(type,'erode')
    erosion = 1;
elseif strcmp(type,'dilate')
    erosion = 0;
else
    error('type must be ''erode'' or ''dilate''')
end

if nargin < 4
    op_fact = 1;
elseif nargin < 3
    conn = 6;
elseif nargin < 2
    error('Not enough input arguments')
end

if ~ismember(conn,[6 18 26])
    error('Argument ''conn'' should be 6, 18 or 26')
end

if ~islogical(X)
    X(isnan(X(:))) = 0;
    X = logical(X);
end

% neighbors
face_neighbors   = [1 0 0;0 1 0; 0 0 1;-1 0 0;0 -1 0;0 0 -1];

if conn > 6
    edge_neighbors   = [1 1 0;1 0 1;0 1 1;...
        -1 1 0;-1 0 1;0 -1 1;1 -1 0;1 0 -1;0 1 -1;...
        -1 -1 0;-1 0 -1; 0 -1 -1];
else
    edge_neighbor_coords = [];
end
if conn == 26
    vertex_neighbors = [1 1 1;1 -1 1;1 1 -1;-1 1 1;...
        -1 -1 1;-1 1 -1;1 -1 -1;-1 -1 -1];
else
    vertex_neighbor_coords = [];
end
if ndims(X) == 2
    sizeX = [size(X) 1];
elseif ndims(X) == 3
    sizeX = size(X);
else
    error('Only works with 2D or 3D matrices')
end

if erosion
    X = ~X;
end
X = double(X);


for it = 1:op_fact
    for i = 1:sizeX(1)
        for j = 1:sizeX(2)
            for k = 1:sizeX(3)
                if X(i,j,k) == 1
                    voxel_coord = [i j k];               
                    face_neighbor_coords = list_neighbor_coords(sizeX,voxel_coord,face_neighbors);
                    if conn > 6
                        edge_neighbor_coords = list_neighbor_coords(sizeX,voxel_coord,edge_neighbors);
                    end
                    if conn == 26
                        vertex_neighbor_coords = list_neighbor_coords(sizeX,voxel_coord,vertex_neighbors);
                    end
                    n_coords = [face_neighbor_coords;edge_neighbor_coords;vertex_neighbor_coords];
                    for n = 1:size(n_coords,1)
                        if ~X(n_coords(n,1),n_coords(n,2),n_coords(n,3))
                            X(n_coords(n,1),n_coords(n,2),n_coords(n,3)) = 2;
                        end
                    end
                end
            end
        end
    end
    X(X==2) = 1;
end

X = logical(X);
if erosion
    X = ~X;
end

% Subfunction
function neighbor_coords = list_neighbor_coords(sizeX,voxel_coord,neighbors_type)

neighbor_coords = neighbors_type + repmat(voxel_coord,size(neighbors_type,1),1);
neighbor_coords = neighbor_coords(~sum(neighbor_coords<1,2),:);
neighbor_coords = neighbor_coords(~sum(neighbor_coords > repmat(sizeX,size(neighbor_coords,1),1),2),:);





