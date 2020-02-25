#!/usr/bin/env bash
# FSL BET using T1w & T2w images



HELP() {
    cat <<HELP
T1xT2BET. Brain extraction using T1w and T2w images.

Usage: 
    bash ${0##*/} -t1 <T1-input-file> -t2 <T2-input-file> [options]
    
Compulsory arguments:
    -t1           Whole-head T1w image
    -t2           Whole-head T2w image (use -aT2 if T2w image is not in the T1w space)
    
Optional arguments:
    -os <suffix>  Suffix for the brain masked images (default is "_BET")
    -aT2          Will coregrister T2w to T1w using flirt. Output will have the suffix provided.
                  Will only work for spatially close images.
    -as           Suffix for T2w to T1w registration ("-in-T1w" if not specified)
    -n <n>        n = the number of iterations BET will be run to find center of gravity (n=1 if option -n is absent).
    -m            Will output the BET mask at the format "'output_prefixT1'_mask.nii.gz"
    -ms <suffix>  Suffix for the mask (default is "_mask")
    -c <c>        Will crop the inputs & outputs after brain extraction. 'c' is the space between the brain and the
                  limits of the crop box expressed in percentage of the brain size (eg. if the brain size is 200 voxels
                  in one dimension and c=10: the sides of the brain in this dimension will be 20 voxels away from the borders
                  of the resulting crop box in this dimension).
    -cs <suffix>  Suffix for the cropped images (default is "_cropped")
    -f <f>        -f options of BET:
                  fractional intensity threshold (0->1); default=0.5; smaller values give larger brain outline estimates
    -g <g>        -g options of BET:
                  vertical gradient in fractional intensity threshold (-1->1); default=0; positive values give larger brain outline at bottom, smaller at top
    -cog <x y z>  For difficult cases, you can directly provide a center of gravity. Only one iteration will be performed.
    -A2           -A2 option of BET. Will be run during last iteration only:
                  run bet2 and then betsurf to get additional skull and scalp surfaces
    -k            Will keep temporary files.
    -p <p>        Prefix for running FSL functions (can be a path or just a prefix)
    
HELP
}

#/********************/
#/********************/

if [[ $# -eq 0 ]]; then
  HELP >&2
  exit 1
fi

# Defaults
AT2="No"
AT2_SUFFIX="-in-T1w"
FSLPREFIX=""
NITER=1
OMASK="No"
BETF=0.5
BETG=0
BETA="No"
KTMP="No"
CROPPING="No"
OUT_SUFFIX="_BET"
CROP_SUFFIX="_cropped"
MASK_SUFFIX="_mask"
Icog=""



ARGS="$@"
SYN=">> Incorrect syntax. See -help"

while [ "$#" -gt 0 ]
do
  case "$1" in

    -t1 | -T1 )
    if [[ -n "$2" ]]; then T1="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -t2 |-T2 )
    if [[ -n "$2" ]]; then T2="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -os |-OS )
    if [[ -n "$2" ]]; then OUT_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -at2 |-aT2 |-AT2 |-At2 )
    AT2="Yes"
    shift
    ;;
    -as |-AS )
    if [[ -n "$2" ]]; then AT2_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -cs |-CS )
    if [[ -n "$2" ]]; then CROP_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -n |-N )
    if [[ -n "$2" ]]; then NITER="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -m |-M )
    OMASK="Yes"
    shift
    ;;
    -ms |-MS )
    if [[ -n "$2" ]]; then MASK_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -c |-C )
    if [[ -n "$2" ]]; then CROP_P="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -f |-F )
    if [[ -n "$2" ]]; then BETF="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -g |-G )
    if [[ -n "$2" ]]; then BETG="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -cog |-COG )
    if [[ -n "$2" && -n "$3" && -n "$4" ]]; then 
      Icog="$2 $3 $4"
    else
      echo $SYN
      exit 1
    fi
    shift 4
    ;;
    -a2 |-A2 )
    BETA="Yes"
    shift
    ;;
    -k |-K )
    KTMP="Yes"
    shift
    ;;
    -p |-P )
    if [[ -n "$2" ]]; then FSLPREFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -help|--help)
    HELP >&2
    exit 1
    shift
    ;;
    *)
    if [[ $arguments -eq 0 ]] && [[ "$1" != "" ]]
    then
    echo "${0##*/} >> Unknown argument '$1'. See -help." >&2;
    exit 1
    fi
    shift 1
    ;;
  esac
done






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
T1name=`extract_base_name $T1`
T2name=`extract_base_name $T2`
INpath=$PWD/
#INpath=`extract_path $T1`

OUT_PREFIX1="${INpath}${T1name}${OUT_SUFFIX}"
OUT_PREFIX2="${INpath}${T2name}${OUT_SUFFIX}"


# **************************

if [[ -n "$CROP_P" ]]; then
  CROPPING="Yes"
fi





cat <<REPORTPARAMETERS

--------------------------------------------------------------------------------------
 Parameters
--------------------------------------------------------------------------------------

 T1 input file:      $T1
 T2 input file:      $T2
 T1 output prefix:   $OUT_PREFIX1
 T2 output prefix:   $OUT_PREFIX2
 Coregister T2w:     $AT2 $AT2_SUFFIX
 Num of iterations:  $NITER
 Output mask:        $OMASK $MASK_SUFFIX
 Cropping:           $CROPPING $CROP_P $CROP_SUFFIX
 BET -f:             $BETF
 BET -g:             $BETG
 Initial COG:        $Icog
 BET -A2:            $BETA
 Keep tmp files:     $KTMP
 FSL prefix:         $FSLPREFIX
======================================================================================

REPORTPARAMETERS



# Temp files
if [[ "$OSTYPE" == "darwin" ]]; then # if macOSX
  declare -a TMP # temporary files
else
  declare -A TMP # temporary files
fi

TMP[T1mulT2]="${INpath}${T1name}_T1mulT2.nii.gz"
TMP[T1mulT2_temp]="${INpath}${T1name}_T1mulT2_temp.nii.gz"
TMP[T1mulT2_pow]="${INpath}${T1name}_T1mulT2_pow.nii.gz"
TMP[T1mulT2_BET]="${INpath}${T1name}_T1mulT2_BET.nii.gz"
TMP[T1mulT2_BET_mask]="${INpath}${T1name}_T1mulT2_BET_mask.nii.gz"
TMP[T1mulT2_masked]="${INpath}${T1name}_T1mulT2_masked.nii.gz"




# FLIRT T2w in T1W if needed
if [[ $AT2 == "Yes" ]]; then
  echo "Coregistering T2w image to T1w space..."
  regT2="${INpath}${T2name}${AT2_SUFFIX}.nii.gz"
  "${FSLPREFIX}flirt" -in $T2 -ref $T1 -dof 6 -cost normmi -out $regT2
  T2=$regT2
fi



# Multiplying T1w & T2w images
echo "Multiplying T1w & T2w images..."
"${FSLPREFIX}fslmaths" $T1 -mul $T2 -abs -sqrt ${TMP[T1mulT2]} -odt float


# BET
if [[ $NITER -gt 0 ]]; then
  cp ${TMP[T1mulT2]} ${TMP[T1mulT2_temp]}
  for ((i = 1 ; i  <= $NITER ; i++)); do
    echo "BETing T1xT2 iteration #$i..."
    if [[ -n "$Icog" ]]; then # Initial COG
      cog=$Icog
      i=$(($NITER+1))
    else
      "${FSLPREFIX}fslmaths" ${TMP[T1mulT2_temp]} -mul ${TMP[T1mulT2_temp]} ${TMP[T1mulT2_pow]} # square values
      cog=`"${FSLPREFIX}fslstats" ${TMP[T1mulT2_pow]} -C`
    fi
    echo "cog: $cog"
    
    if [[ $BETA == "Yes" && $i -eq $NITER ]]; then # - A2 option
      echo "Running BET on T1w image with -A2 option..."
      "${FSLPREFIX}bet" $T1 $OUT_PREFIX1 -c $cog -f $BETF -g $BETG -A2 $T2
      echo "Doing last BET T1w x T2w image..."
    fi
    
    "${FSLPREFIX}bet" ${TMP[T1mulT2_temp]} ${TMP[T1mulT2_BET]} -m -c $cog -f $BETF -g $BETG
    mv ${TMP[T1mulT2_BET]} ${TMP[T1mulT2_temp]}
  done
else
  echo "Error: number of iterations must be a positive number"
  exit 1
fi

# Applying BET mask
echo "Applying BET mask to images..."
"${FSLPREFIX}fslmaths" $T1 -mas ${TMP[T1mulT2_BET_mask]} $OUT_PREFIX1
"${FSLPREFIX}fslmaths" $T2 -mas ${TMP[T1mulT2_BET_mask]} $OUT_PREFIX2
if [[ $OMASK == "Yes" ]]; then
  mv ${TMP[T1mulT2_BET_mask]} "${OUT_PREFIX1}${MASK_SUFFIX}.nii.gz"
fi



# Crop images


if [[ -n "$CROP_P" ]]; then
  echo "Cropping..."
  SCRIPTpath=`extract_path $0`
  if [[ -n "$FSLPREFIX" ]]; then
    FPOPT="-p ${FSLPREFIX}"
  fi
  if test -f "${SCRIPTpath}CropVolume.sh"; then # check if Cropping scripts exists
    echo "Calling ${SCRIPTpath}CropVolume.sh"

    bash "${SCRIPTpath}CropVolume.sh" -i $T1 -i $T2 -i "$OUT_PREFIX1.nii.gz" -i "$OUT_PREFIX2.nii.gz" -b $OUT_PREFIX1 -c $CROP_P -s $CROP_SUFFIX -d $FPOPT
    if [[ $OMASK == "Yes" ]]; then
      bash "${SCRIPTpath}CropVolume.sh" -i "${OUT_PREFIX1}${MASK_SUFFIX}.nii.gz" -b $OUT_PREFIX1 -c $CROP_P -s $CROP_SUFFIX -d $FPOPT
      rm "${OUT_PREFIX1}${MASK_SUFFIX}.nii.gz"
    fi
  else # else do it here
    roi=`"${FSLPREFIX}fslstats" $OUT_PREFIX1 -w` # get smallest roi of non zero voxels
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
      DIM_SIZE=`"${FSLPREFIX}fslval" $OUT_PREFIX1 ${DIM_KEYS[$i]}` # get size of volume in this dimension
      
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

    # Crop with fslroi
    "${FSLPREFIX}fslroi" $OUT_PREFIX1 "${OUT_PREFIX1}${CROP_SUFFIX}" ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
    "${FSLPREFIX}fslroi" $OUT_PREFIX2 "${OUT_PREFIX2}${CROP_SUFFIX}" ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
    "${FSLPREFIX}fslroi" $T1 "${INpath}${T1name}${CROP_SUFFIX}" ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
    "${FSLPREFIX}fslroi" $T2 "${INpath}${T2name}${CROP_SUFFIX}" ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
  
  
  
    if [[ $OMASK == "Yes" ]]; then
      "${FSLPREFIX}fslroi" "${OUT_PREFIX1}${MASK_SUFFIX}" "${OUT_PREFIX1}${MASK_SUFFIX}${CROP_SUFFIX}" ${C_MIN[0]} ${C_SIZE[0]} ${C_MIN[1]} ${C_SIZE[1]} ${C_MIN[2]} ${C_SIZE[2]}
      rm "${OUT_PREFIX1}${MASK_SUFFIX}.nii.gz"
    fi
  fi
  rm "${OUT_PREFIX1}.nii.gz"
  rm "${OUT_PREFIX2}.nii.gz"
fi




# Remove all temporary files
if [[ $KTMP == "No" ]]; then
  for key in ${!TMP[@]}; do
    if test -f "${TMP[$key]}"; then
      rm ${TMP[$key]}
    fi
  done
fi


exit 0




