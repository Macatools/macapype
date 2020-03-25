#!/usr/bin/env bash
# Bias field correction using T1w & T2w images



HELP() {
    cat <<HELP
T1xT2BiasFieldCorrection. Bias field correction using T1w & T2w images. Provides an attempt of brain extration if wanted.

Usage: 
    bash ${0##*/} -t1 <T1-input-file> -t2 <T2-input-file> [options]
    
Compulsory arguments:
    -t1           Whole-head T1w image
    -t2           Whole-head T2w image (use -aT2 if T2w image is not in the T1w space)
    
Optional arguments:
    -os <suffix>  Suffix for the bias field corrected images (default is "_debiased")
    -aT2          Will coregrister T2w to T1w using flirt. Output will have the suffix provided.
                  Will only work for spatially close images.
    -as           Suffix for T2w to T1w registration ("-in-T1w" if not specified)
    -s <s>        size of gauss kernel in mm when performing mean filtering (default=4)
    -b <mask>     Brain or brain mask file. Will also output bias corrected brain files with the format "output_prefix_brain.nii.gz"
    -bet <n>      Will try to "smart" BET the anat files to get a brain mask: n = the number of iterations BET will be run
                  to find center of gravity (default=0, will not BET if option -b has been specified).
                  Will also output bias corrected brain files and the BET mask
    -bs <suffix>  Suffix for the BET masked images (default is "_BET")
    -f <f>        -f options of BET:
                  fractional intensity threshold (0->1); default=0.5; smaller values give larger brain outline estimates
    -g <g>        -g options of BET:
                  vertical gradient in fractional intensity threshold (-1->1); default=0; positive values give larger brain outline at bottom, smaller at top
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
SIGMA=4
BRAIN=""
FSLPREFIX=""
TRYBET=0
BETF=0.5
BETG=0
KTMP="No"
AT2_SUFFIX="-in-T1w"
OUT_SUFFIX="_debiased"
BET_SUFFIX="_BET"

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
    -s |-S )
    if [[ -n "$2" ]]; then SIGMA="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -b |-B )
    if [[ -n "$2" ]]; then BRAIN="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -bet |-BET )
    if [[ -n "$2" ]]; then TRYBET="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -bs |-BS )
    if [[ -n "$2" ]]; then BET_SUFFIX="$2"; else echo $SYN; exit 1 ; fi
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
T1name=`extract_base_name $T1`
T2name=`extract_base_name $T2`
#INpath=`extract_path $T1`
INpath=$PWD/
OUT_PREFIX1="${INpath}${T1name}${OUT_SUFFIX}"
OUT_PREFIX2="${INpath}${T2name}${OUT_SUFFIX}"

# **************************






cat <<REPORTPARAMETERS

--------------------------------------------------------------------------------------
 Bias correction parameters
--------------------------------------------------------------------------------------

 T1 input file:      $T1
 T2 input file:      $T2
 T1 output prefix:   $OUT_PREFIX1
 T2 output prefix:   $OUT_PREFIX2
 Coregister T2w:     $AT2 $AT2_SUFFIX
 Sigma:              $SIGMA
 Brain mask:         $BRAIN
 Try BETing:         $TRYBET $BET_SUFFIX
 BET -f:             $BETF
 BET -g:             $BETG
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
TMP[T1mulT2_norm]="${INpath}${T1name}_T1mulT2_norm.nii.gz"
TMP[T1mulT2_smooth]="${INpath}${T1name}_T1mulT2_smooth.nii.gz"
TMP[T1mulT2_NM]="${INpath}${T1name}_T1mulT2_NM.nii.gz"
TMP[T1mulT2_mod]="${INpath}${T1name}_T1mulT2_mod.nii.gz"
TMP[T1mulT2_mod_mask]="${INpath}${T1name}_T1mulT2_mod_mask.nii.gz"
TMP[bias_raw]="${INpath}${T1name}_bias_raw.nii.gz"
TMP[OutputBiasField]="${INpath}${T1name}_OutputBiasField.nii.gz"






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


# Brain mask
if [[ -n "$BRAIN" ]]; then
  echo "Applying brain mask..."
  "${FSLPREFIX}fslmaths" ${TMP[T1mulT2]} -mas $BRAIN ${TMP[T1mulT2_masked]}
elif [[ $TRYBET -ne 0 ]]; then
  cp ${TMP[T1mulT2]} ${TMP[T1mulT2_temp]}
  for ((i = 1 ; i  <= $TRYBET ; i++)); do
    echo "BETing T1xT2 iteration #$i..."
    "${FSLPREFIX}fslmaths" ${TMP[T1mulT2_temp]} -mul ${TMP[T1mulT2_temp]} ${TMP[T1mulT2_pow]} # square values
    cog=`"${FSLPREFIX}fslstats" ${TMP[T1mulT2_pow]} -C`
    echo "cog: $cog"
    "${FSLPREFIX}bet" ${TMP[T1mulT2_temp]} ${TMP[T1mulT2_BET]} -m -c $cog -f $BETF -g $BETG
    mv ${TMP[T1mulT2_BET]} ${TMP[T1mulT2_temp]}
  done
  "${FSLPREFIX}fslmaths" ${TMP[T1mulT2]} -mas ${TMP[T1mulT2_BET_mask]} ${TMP[T1mulT2_masked]}
else
  mv ${TMP[T1mulT2]} ${TMP[T1mulT2_masked]}
fi


# Mean intensity value
meanintval=`"${FSLPREFIX}fslstats" ${TMP[T1mulT2_masked]} -M`
echo "Mean intensity value = $meanintval"



# Debiasing operations
echo Normalizing...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_masked]} -div $meanintval ${TMP[T1mulT2_norm]}
echo Smoothing...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_norm]} -bin -s $SIGMA ${TMP[T1mulT2_smooth]}
echo Normalizing...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_norm]} -s $SIGMA -div ${TMP[T1mulT2_smooth]} ${TMP[T1mulT2_NM]}
echo Modulate...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_norm]} -div ${TMP[T1mulT2_NM]} ${TMP[T1mulT2_mod]}

STD=`"${FSLPREFIX}fslstats" ${TMP[T1mulT2_mod]} -S`
MEAN=`"${FSLPREFIX}fslstats" ${TMP[T1mulT2_mod]} -M`
Lower=`echo "$MEAN - ($STD * 0.5)" | bc -l`
echo "Lower = $Lower"

echo Masking...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_mod]} -thr $Lower -bin -ero -mul 255 ${TMP[T1mulT2_mod_mask]}
echo Dilating...
"${FSLPREFIX}fslmaths" ${TMP[T1mulT2_norm]} -mas ${TMP[T1mulT2_mod_mask]} -dilall ${TMP[bias_raw]} -odt float
echo Smoothing...
"${FSLPREFIX}fslmaths" ${TMP[bias_raw]}  -s $SIGMA ${TMP[OutputBiasField]}
echo Applying bias field...
"${FSLPREFIX}fslmaths" $T1 -div ${TMP[OutputBiasField]} $OUT_PREFIX1 -odt float
"${FSLPREFIX}fslmaths" $T2 -div ${TMP[OutputBiasField]} $OUT_PREFIX2 -odt float

# Applying brain or BET mask to debiased images
if [[ -n "$BRAIN" ]]; then
  echo "Applying brain mask to debiased images..."
  "${FSLPREFIX}fslmaths" $OUT_PREFIX1 -mas $BRAIN "${OUT_PREFIX1}_brain"
  "${FSLPREFIX}fslmaths" $OUT_PREFIX2 -mas $BRAIN "${OUT_PREFIX2}_brain"
elif [[ $TRYBET -ne 0 ]]; then
  echo "Applying BET mask to debiased images..."
  "${FSLPREFIX}fslmaths" $OUT_PREFIX1 -mas ${TMP[T1mulT2_BET_mask]} "${OUT_PREFIX1}${BET_SUFFIX}"
  "${FSLPREFIX}fslmaths" $OUT_PREFIX2 -mas ${TMP[T1mulT2_BET_mask]} "${OUT_PREFIX2}${BET_SUFFIX}"
  mv ${TMP[T1mulT2_BET_mask]} "${OUT_PREFIX1}${BET_SUFFIX}_mask.nii.gz"
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




