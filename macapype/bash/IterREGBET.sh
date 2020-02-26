#!/usr/bin/env bash
# IterREGBET. Iterative registration of the in-file to the ref file (registered brain mask of the ref image is used at each iteration).
# To use when the input brain mask is not optimal (eg. an output of FSL BET).
# Will output a better brain mask of the in-file.



HELP() {
    cat <<HELP
IterREGBET. Iterative registration of the in-file to the ref file (registered brain mask of the ref image is used at each iteration).
To use when the input brain mask is not optimal (eg. an output of FSL BET).
Will output a better brain mask of the in-file.

Usage: 
    bash ${0##*/} -in <moving-whole-head-image> -inb <moving-brain-image> -ref <ref-brain-image> -o <output-prefix> [options]
    
Compulsory arguments:
    -inw  <file>   Moving whole-head image
    -inb  <file>   Moving brain image
    -refb <file>   Fixed reference brain image
    
Optional arguments:
    -xp <prefix>  Prefix for the registration outputs ("in_FLIRT-to_ref" if not specified)
    -bs <suffix>  Suffix for the brain files ("in_IRbrain" & "in_IRbrain_mask" if not specified)
    -dof <dof>    FLIRT degrees of freedom (6=rigid body, 7=scale, 12=affine{default}). Use dof 6 for intra-subject, 12 for inter-subject registration
    -cost <cost>  FLIRT cost {mutualinfo,corratio,normcorr,normmi,leastsq,labeldiff,bbr}    (default is normmi)
    -n <n>        n = the number of FLIRT iterations (>=2, default=2).
    -m <method>   At each new iteration, either use:
                    - m=ref, the reference brain mask (default)
                    - m=union, the union of the reference and input brain masks (use if your input brain is too small)
                    - m=inter , the intersection of the reference and input brain masks (use if your input brain is too big)
                    - m=mix, a mix between union & intersection (give it a try!)
    -refw <file>  Do a whole-head non-linear registration (using FNIRT) during last iteration (provide reference whole-head image)
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
DOF=12
COST="normmi"
FSLPREFIX=""
NITER=2
OUT_PREFIX=""
METHOD="ref"
REF_WHOLE=""
KTMP="No"
BET_SUFFIX="_IRbrain"


ARGS="$@"
SYN=">> Incorrect syntax. See -help"

while [ "$#" -gt 0 ]
do
  case "$1" in

    -inw | -INW )
    if [[ -n "$2" ]]; then IN_WHOLE="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -inb |-INB )
    if [[ -n "$2" ]]; then IN_BRAIN="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -refb |-REFB )
    if [[ -n "$2" ]]; then REF_BRAIN="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -refw |-REFW )
    if [[ -n "$2" ]]; then REF_WHOLE="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -xp |-XP )
    if [[ -n "$2" ]]; then OUT_PREFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -bs |-BS )
    if [[ -n "$2" ]]; then BET_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -dof |-DOF )
    if [[ -n "$2" ]]; then DOF="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -n |-N )
    if [[ -n "$2" ]]; then NITER="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -cost |-COST )
    if [[ -n "$2" ]]; then COST="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -m |-M )
    if [[ -n "$2" ]]; then METHOD="$2"; else echo $SYN; exit 1 ; fi
    shift 2
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
    echo ">> Unknown argument '$1'. See -help." >&2;
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
IN_BRAINname=`extract_base_name $IN_BRAIN`
IN_WHOLEname=`extract_base_name $IN_WHOLE`
#INpath=`extract_path $IN_BRAIN`
INpath=$PWD/

REFname=`extract_base_name $REF_BRAIN`
if [[ -z $OUT_PREFIX ]]; then
  OUT_PREFIX="${INpath}${IN_BRAINname}_FLIRT-to_${REFname}"
fi
I2R_XFM="${OUT_PREFIX}.xfm"
R2I_XFM="${OUT_PREFIX}_inverse.xfm"
IN_OUT_BRAIN="${INpath}${IN_WHOLEname}${BET_SUFFIX}"
IN_OUT_MASK="${INpath}${IN_WHOLEname}${BET_SUFFIX}_mask"

# **************************



# **************************
# Check options
case "$METHOD" in
  ref);;
  union);;
  inter);;
  mix);;
  *)
  echo "-m (method) option must be one of the following:"
  echo "ref, union, inter or mix"
  exit 1
  ;;
esac

# **************************


cat <<REPORTPARAMETERS

--------------------------------------------------------------------------------------
 Parameters
--------------------------------------------------------------------------------------

 Whole-head moving image:   $IN_WHOLE
 Brain moving image:        $IN_BRAIN
 Reference brain:           $REF_BRAIN
 Whole-head reference:      $REF_WHOLE
 Registration prefix:       $OUT_PREFIX
 Output brain prefix:       $IN_OUT_BRAIN
 FLIRT DOF:                 $DOF
 FLIRT iterations:          $NITER
 Method:                    $METHOD
 Cost function:             $COST
 Keep tmp files:            $KTMP
 FSL prefix:                $FSLPREFIX
======================================================================================

REPORTPARAMETERS



# **************************
if [[ "$OSTYPE" == "darwin" ]]; then # if macOSX
  declare -a TMP # temporary files
  declare -a WARP # warp files
else
  declare -A TMP # temporary files
  declare -A WARP # warp files
fi


# binarize in brain
if [[ $METHOD != "ref" ]]; then
  TMP[PREV_MASK]="${INpath}${IN_BRAINname}_mask.nii.gz"
  "${FSLPREFIX}fslmaths" $IN_BRAIN -bin ${TMP[PREV_MASK]} # binarize in brain (as previous mask)
fi
# Masks for mix method
if [[ $METHOD == "mix" ]]; then
  TMP[UNION_MASK]="${INpath}${IN_BRAINname}_unionmask.nii.gz"
  TMP[INTER_MASK]="${INpath}${IN_BRAINname}_intermask.nii.gz"
  TMP[EROUN_MASK]="${INpath}${IN_BRAINname}_erounmask.nii.gz"
fi

# binarize ref brain
TMP[REF_MASK]="${INpath}${REFname}_mask.nii.gz"
"${FSLPREFIX}fslmaths" $REF_BRAIN -bin ${TMP[REF_MASK]} # binarize ref brain


# Extra whole-head registration files
if [[ -n $REF_WHOLE ]]; then
  if test -f "$REF_WHOLE"; then
    WARP[WH_OUT]="${OUT_PREFIX}_Warped"
    WARP[WH_WARP]="${OUT_PREFIX}_Warp"
    WARP[WH_INVWARP]="${OUT_PREFIX}_InverseWarp"
  else
    echo Whole-head reference
    echo $REF_WHOLE
    echo does not exist
    exit 1
  fi
fi

# **************************



# FLIRT iterations
for ((i = 1 ; i  <= $NITER ; i++)); do
  echo "FLIRT iteration $i/$NITER..."
  
  # Registration
  "${FSLPREFIX}flirt" -in $IN_BRAIN -ref $REF_BRAIN -cost $COST -omat $I2R_XFM -out $OUT_PREFIX -dof $DOF # compute xfm
  "${FSLPREFIX}convert_xfm" -omat $R2I_XFM -inverse $I2R_XFM # inverse xfm
  
  # Extra whole-head non-linear registration, if wanted
  if [[ -n $REF_WHOLE ]] && [[ $i == $NITER ]]; then
    echo "FNIRT..."
    "${FSLPREFIX}fnirt" --in=$IN_WHOLE --ref=$REF_WHOLE --aff=$I2R_XFM --iout=${WARP[WH_OUT]} --cout=${WARP[WH_WARP]} # compute warp
    echo "Inverting warp..."
    "${FSLPREFIX}invwarp" -r $IN_WHOLE -w ${WARP[WH_WARP]} -o ${WARP[WH_INVWARP]}
    echo "Applying inverse warp..."
    "${FSLPREFIX}applywarp" --ref=$IN_WHOLE --in=${TMP[REF_MASK]} --out=$IN_OUT_MASK --warp=${WARP[WH_INVWARP]} --interp=nn
  else
    "${FSLPREFIX}flirt" -in ${TMP[REF_MASK]} -ref $IN_WHOLE -out $IN_OUT_MASK -interp nearestneighbour -applyxfm -init $R2I_XFM # move brain mask to in_file
  fi
  
  
  
  
  # Mask Brain depending on method
  if [[ $METHOD == "union" ]]; then # Union of previous & current masks
    "${FSLPREFIX}fslmaths" $IN_OUT_MASK -add ${TMP[PREV_MASK]} -bin $IN_OUT_MASK # union mask
    cp "${IN_OUT_MASK}.nii.gz" ${TMP[PREV_MASK]} # replace previous mask by new one
    "${FSLPREFIX}fslmaths" $IN_WHOLE -mas $IN_OUT_MASK $IN_OUT_BRAIN # extract brain from mask
  elif [[ $METHOD == "inter" ]]; then # Intersection of previous & current masks
    "${FSLPREFIX}fslmaths" $IN_OUT_MASK -add ${TMP[PREV_MASK]} -thr 2 $IN_OUT_MASK # intersection mask
    cp "${IN_OUT_MASK}.nii.gz" ${TMP[PREV_MASK]} # replace previous mask by new one
    "${FSLPREFIX}fslmaths" $IN_WHOLE -mas $IN_OUT_MASK $IN_OUT_BRAIN # extract brain from mask
  elif [[ $METHOD == "mix" ]]; then # Mix of previous & current masks
    "${FSLPREFIX}fslmaths" $IN_OUT_MASK -add ${TMP[PREV_MASK]} -bin ${TMP[UNION_MASK]} # union mask
    "${FSLPREFIX}fslmaths" $IN_OUT_MASK -add ${TMP[PREV_MASK]} -thr 2 ${TMP[INTER_MASK]} # intersection mask
    "${FSLPREFIX}fslmaths" ${TMP[UNION_MASK]} -ero ${TMP[EROUN_MASK]} # erode union mask
    "${FSLPREFIX}fslmaths" ${TMP[INTER_MASK]} -add ${TMP[EROUN_MASK]} -bin $IN_OUT_MASK # union of inter & eroded mask
    cp "${IN_OUT_MASK}.nii.gz" ${TMP[PREV_MASK]} # replace previous mask by new one
    "${FSLPREFIX}fslmaths" $IN_WHOLE -mas $IN_OUT_MASK $IN_OUT_BRAIN # extract brain from mask
  fi
  
  "${FSLPREFIX}fslmaths" $IN_WHOLE -mas $IN_OUT_MASK $IN_OUT_BRAIN # extract brain from mask
  IN_BRAIN=$IN_OUT_BRAIN # point to new brain extration for next iteration input
done



# Remove all temporary files
if [[ $KTMP == "No" ]]; then
  for key in ${!TMP[@]}; do
    if test -f "${TMP[$key]}"; then
      rm ${TMP[$key]}
    fi
  done
fi

exit 0




