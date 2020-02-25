#!/usr/bin/env bash
# Crop Volume based on a brain extraction



HELP() {
    cat <<HELP
CropVolume. Crop image(s) based on a brain extraction. Multiple images can be cropped at once. Will crop each volume preceeded by the -i option

Usage: 
    bash ${0##*/} -i <input-file> -b <brain-file> [options]
    
Compulsory arguments:
    -i <input>  Volume to crop (you can specify as many -in as you want)
    -b <input>  Brain image or brain mask, in the same space as the in-file(s)
    
Optional arguments:
    -o <prefix> Prefix for the cropped image(s) (Must provide as many prefixes as input images with -o, default is the base name of each input image).
    -s <suffix> Suffix for the cropped image(s) (default is "_cropped")
    -c <c>      'c' is the space between the brain and the limits of the crop box expressed in percentage of
                the brain size (eg. if the brain size is 200 voxels in one dimension and c=10: the sides of
                the brain in this dimension will be 20 voxels away from the borders of the resulting
                crop box in this dimension). Default: c=10
    -p <p>      Prefix for running FSL functions (can be a path or just a prefix)
    
HELP
}

#/********************/
#/********************/


if [[ "$1" == "-h" || "$1" == "-help" || "$1" == "-H" || $# -eq 0 ]]; then
  HELP >&2
  exit 1
fi


# Defaults
IN_FILES=()
OUT_PREFIXES=()
OUT_SUFFIX="_cropped"
FSLPREFIX=""
CROP_P=10;
NO_DISP_PAR=""


# reading command line arguments
while getopts "i:I:b:B:o:O:s:S:c:C:p:P:d" OPT
  do
  case $OPT in
      i |I)  # input images
   IN_FILES[${#IN_FILES[@]}]=$OPTARG
   ;;
      b |B)  # brain file
   IN_BRAIN=$OPTARG
   ;;
      o |O) #output name prefix
   OUT_PREFIXES[${#OUT_PREFIXES[@]}]=$OPTARG
   ;;
      s |S) #output name prefix
   OUT_SUFFIX=$OPTARG
   ;;
      c |C)  # crop percentage
   CROP_P=$OPTARG
   ;;
      p |P)  # fsl prefix
   FSLPREFIX=$OPTARG
   ;;
      d)  # do not display parameters
   NO_DISP_PAR=1
   ;;
     :) # getopts issues an error message
   echo "${0##*/} >> Bad usage. $OPTARG requires an argument" 1>&2
   exit 1
   ;;
     \?) # getopts issues an error message
   echo "${0##*/} >> See -help." 1>&2
   exit 1
   ;;
  esac
done



if [[ -z $IN_FILES || -z $IN_BRAIN ]]; then
  echo "${0##*/} >> Missing arguments"
  echo ">> See -help." 1>&2
  exit 1
fi



# **************************
# Functions

extract_base_name() {
IN=$1
INext=${IN##*.}
local INbase=""
if [[ $INext == "gz" ]]; then
  INngz=${IN%.gz}
  INext=".${INngz##*.}.gz"
  INbase=${IN%$INext}
else
  INext=".${INext}"
  INbase=${IN%$INext}  
fi
INbase=${INbase##*/}
echo $INbase
}

extract_path() {
IN=$1
BASE=${IN##*/}  # base
local DIR=${IN%$BASE}  # dirpath
echo $DIR
}

# *************************




# *************************
# Files

if [[ -n $OUT_PREFIXES ]]; then # check if the number of prefixes is equal to the number of input images
  if [[ ${#IN_FILES[@]} -ne ${#OUT_PREFIXES[@]} ]]; then
    echo "Number of prefixes (-o) is not equal to the number of input images (-i)."
    exit 1
  fi
else # if no prefix provided, create them
  for(( i=0; i<${#IN_FILES[@]}; i++ )); do
    INname=`extract_base_name ${IN_FILES[$i]}`
    INpath=`extract_path ${IN_FILES[$i]}`
    OUT_PREFIXES[$i]="$PWD/${INname}${OUT_SUFFIX}"
  done
fi

# **************************




if [[ -z $NO_DISP_PAR ]]; then

cat <<PARB

--------------------------------------------------------------------------------------
 Parameters
--------------------------------------------------------------------------------------

PARB

for(( i=0; i<${#IN_FILES[@]}; i++ )); do
  echo " Input file:         ${IN_FILES[$i]}"
done
echo " Brain file:         $IN_BRAIN"
for(( i=0; i<${#OUT_PREFIXES[@]}; i++ )); do
  echo " Output file:        ${OUT_PREFIXES[$i]}.nii.gz"
done

cat <<PARE
 Percent cropping:   $CROP_P
 FSL prefix:         $FSLPREFIX
======================================================================================

PARE

fi


# Crop images

echo "Cropping..."
roi=`"${FSLPREFIX}fslstats" $IN_BRAIN -w` # get smallest roi of non zero voxels
IFS=' ' read -ra Aroi <<< "$roi" # parse $roi with IFS delimiter ' '

DIM_NAMES=('X' 'Y' 'Z')
DIM_KEYS=('dim1' 'dim2' 'dim3')
for ((i = 0 ; i <= 2 ; i++)); do
  ROI_MIN=${Aroi[$(($i * 2))]}
  ROI_SIZE=${Aroi[$((($i * 2) + 1))]}
  C_SPACE=$(($ROI_SIZE * $CROP_P / 100)) # Space between brain and crop box in each dimension, in voxels
  echo "Space between brain and crop box will be $C_SPACE voxels in dimension ${DIM_NAMES[$i]}"
  C_MIN[$i]=$(($ROI_MIN - $C_SPACE)) # lower bound of crop box
  C_MAX=$(($ROI_MIN + $ROI_SIZE + $C_SPACE - 1)) # higher bound of crop box
  DIM_SIZE=`"${FSLPREFIX}fslval" $IN_BRAIN ${DIM_KEYS[$i]}` # get size of volume in this dimension
  
  # Check that roi is not out of bounds
  if [[ ${C_MIN[$i]} -lt 0 ]]; then
    C_MIN[$i]=0
  fi
  if [[ $C_MAX -ge $DIM_SIZE ]]; then
    C_MAX=$(($DIM_SIZE - 1))
  fi
  C_SIZE[$i]=$(($C_MAX + 1 - ${C_MIN[$i]}))
   echo "${DIM_NAMES[$i]}min = ${C_MIN[$i]}, ${DIM_NAMES[$i]}size = ${C_SIZE[$i]}"
done

echo
# Crop with fslroi
for(( i=0; i<${#IN_FILES[@]}; i++ )); do
  echo "Cropping ${IN_FILES[$i]}..."
  echo ${IN_FILES[$i]} ${OUT_PREFIXES[$i]}
  "${FSLPREFIX}fslroi" ${IN_FILES[$i]} ${OUT_PREFIXES[$i]} ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
done


exit 0




