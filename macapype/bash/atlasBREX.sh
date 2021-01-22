#!/usr/bin/env bash

#atlasBREX: Automated template-derived brain extraction for animal MRI
#https://github.com/jlohmeier/atlasBREX
#LIC: BSD-3-Clause
#Author: Johannes Lohmeier
#Email: johannes.lohmeier@charite.de
#Changed: 31.10.2020 (v1.5)


#Number of threads for ANTs
#set number of threads: ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=32
#NPROCESSORS_ONLN on FreeBSD/PC-BSD
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=$(/bin/sh -c 'getconf _NPROCESSORS_ONLN')
 # controls multi-threading
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS

HELP() {
    cat <<HELP

atlasBREX [ver: 1.5]
--- 
Documentation: https://github.com/jlohmeier/atlasBREX
Requirement: FSL ≥ 5 (optional usage of AFNI and ANTs)
---

Usage: 

    bash $0 -b <input> -nb <input> -h <input> -f <input>

Compulsory arguments:

    -b          brain-extracted atlas or template
    -nb         whole-head (non-brain) atlas or template
    -h          target 3D volume
    -f          fractional intensity threshold [1 > n > 0] for provisional (BET) brain-extraction (e.g. -f 0.2).
                interactive pilot: [-f n] proposes 3 default thresholds for user selection. 
                for multi-step registration, different values for high-res, 
                low-res and native volumes can be entered (e.g. -f 0.2,0.5,0.8)

Optional arguments:

    -l          low-resolution 3D volume (3-step registration)
    -n          (functional) 3D/4D volume  (2-/3-step registration)
    -t/-tmp     disable removal [1] of temporary files (default: 0) 
    -w/-wrp     define FNIRT (FSL) warp-resolution (e.g. -wrp 10,10,10),
                for SyN (ANTs) enter warp [-wrp 1] flag (e.g. -wrp 1 -reg 2)
    -r/-reg     FNIRT w/ bending- [-reg 0] or membrane-energy regularization [-reg 1] 
                ANTs/SyN w/ [-reg 2] or w/o [-reg 3] additional N4BiasFieldCorrection (def: 1)
    -nrm        provisional intensity normalization w/ T1 [-nrm 1] or T2 [-nrm 2] (req: AFNI)
                (recommended for low-resolution volumes)
    -lr         optimized parameter settings for low-resolution volumes:
                [1] non-linear registration between whole-head template and target volume with mask
                [2] non-linear registration based on skullstripped template and target volume (def: 0)
    -msk        mask binarization threshold (in %) for fslmaths 
                w/ optional erosion and dilation (e.g. -msk b,10,0,0) (def: b,0.5,0,0)
                [-msk b,[100 < n > 0] for threshold, [0-9] for n-times erosion,
                [0-9] for n-times dilation] or 3dAutomask (e.g. -msk a,0,0, req: AFNI) 
                [-msk a,[0-9] for n-times erosion,[0-9] for n-times dilation]
    -vox        provisional voxel-size adjustment [-vox 1] (def: 0)
    -dil        n-times dilation of the brain-extraction from linear registration 
                prior to non-linear registration (e.g. -dil 4)

HELP
}

#/********************/
#/********************/

if [[ $# -eq 0 ]]
then
    HELP >&2
    exit 1
fi

ARGS="$@"
SYN=">> Incorrect syntax. See -help"

while [ "$#" -gt 0 ]
do
  case "$1" in

    -b | -B )
    if [[ -n "$2" ]]; then standard_BE_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -nb |-NB )
    if [[ -n "$2" ]]; then standard_nonBE_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -h |-H )
    if [[ -n "$2" ]]; then highres_nonBE_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -l |-L )
    if [[ -n "$2" ]]; then lowres_nonBE_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -n |-N )
    if [[ -n "$2" ]]; then func_nonBE_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -f |-F )
    if [[ -n "$2" ]]; then THR_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -r |-R |-reg |-REG )
    if [[ -n "$2" ]]; then METHOD_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -lr |-LR )
    if [[ -n "$2" ]]; then LOWRES_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -w |-W |-wrp |-WRP )
    if [[ -n "$2" ]]; then WARP_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -t |-T |-tmp |-TMP )
    if [[ -n "$2" ]]; then TEMP_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -rot |-ROT )
    if [[ -n "$2" ]]; then REORIENT_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;    
    -msk |-MSK )
    if [[ -n "$2" ]]; then MASK_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -nrm |-NRM )
    if [[ -n "$2" ]]; then NORM_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -vox |-VOX )
    if [[ -n "$2" ]]; then VOX_="$2"; else echo $SYN; exit 1 ; fi
    shift 2
    ;;
    -dil |-DIL )
    if [[ -n "$2" ]]; then voxfac_="$2"; else echo $SYN; exit 1 ; fi
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

#error handling
set -o errexit
set -o pipefail
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

removetemp() {
    if [[ $TEMP -eq "0" ]]
    then
        rm -f *'mask'*
        rm -f *'orig'*
        rm -f *'tmp'*
        rm -f *'temp'*
        rm -f *'high2'*
        #keep non-linear warp
        find . -maxdepth 1 -name "*_.nii.gz*" ! -name "*std2high_warp*" -delete
        find . -maxdepth 1 -name "*std2*" ! -name "*.nii.gz" ! -name "*std2high_warp*" -delete
        rm -f *'low2'*
    fi
    }

trap removetemp SIGINT
trap removetemp 0

#/********************/
#/********************/
#/********************/
#/********************/

#prep region
    #compulsory input
    if [[ -z "${standard_BE_}" || -z "${standard_nonBE_}" || -z "${highres_nonBE_}" ]] || [[ -z "${THR_}" ]]
    then
        echo '>> Compulsory parameters were not specified! See -help'
        exit 1
    fi

    #warning not in common folder
    SDIR=$(dirname "$0")
    if [[ ! $(dirname "${standard_BE_}") == $SDIR ]] || [[ ! $(dirname "${standard_nonBE_}") == $SDIR ]] || [[ ! $(dirname "${highres_nonBE_}") == $SDIR ]]
    then
        echo ">> All files need to be within a common folder."
        exit 1
    fi

    #warning conflicting file/folder names
    tfd=$(echo *temp*)
    ofd=$(echo *orig*)
    if [[ -f ${tfd[0]} ]] || [[ -d ${tfd[0]} ]] || [[ -f ${ofd[0]} ]] || [[ -d ${ofd[0]} ]]
    then
        echo ">> Rename files or folders with [temp] or [orig] within this directory."
        exit 1
    fi


    #set temp flag
    TEMP=0
    if [[ -n "${TEMP_}" ]]
    then
        if [[ ${TEMP_} -eq "1" ]] || [[ ${TEMP_} -eq "0" ]]
        then
            #remove temp
            TEMP=${TEMP_}
        else
            echo '>> Input needs to be either [1] or [0] (default: 0). See -help'
            exit 1
        fi
    fi

    #default
    MASK="b,0.5,0,0"
    #(\d?[1-9]|[1-9]0)
    #set mask
    if [[ -n "${MASK_}" ]]
    then
        if [[ ${MASK_} =~ ^a,[0-9]{1},[0-9]{1}$ ]] || [[ ${MASK_} =~ ^b,([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),[0-9]{1},[0-9]{1}$ ]]
        then
            MASK=${MASK_}
            if [[ $(echo $MASK | cut -d"," -f1) == "a" ]]
            then
                if ! type 3dAutomask &>/dev/null
                then
                    echo '>> 3dAutomask was not found. Check your .bashrc profile or reinstall AFNI.'
                    exit 1
                fi
            fi
        else
            echo '>> Specified mask input is not valid. See -help'
            exit 1
        fi
    fi

    #set method
    #FSL default
    METHOD=0
    REGM='membrane_energy'
    if [[ -n "${METHOD_}" ]]
    then
        if [[ $METHOD_ =~ ^[0-4]$ ]]
        then
            case $METHOD_ in
            "0")
             #FSL bending
            METHOD=0
            REGM='bending_energy'
            ;;
            "1")
            #FSL membrane
            METHOD=0
            REGM='membrane_energy'
            ;;
            "2")
            #ANTs w/ BF
            METHOD=1
            BIAS=1
            ;;
            "3")
            #ANTs w/o BF
            METHOD=1
            ;;
            esac
        else
        echo '>> Input needs to be a number from [1-4] (default: 0). See -help'
        exit 1
        fi
    fi

    if [[ $METHOD -eq "1" ]]
    then
        if ! type antsRegistration &>/dev/null || ! type antsApplyTransforms &>/dev/null || ! type antsRegistrationSyN.sh &>/dev/null  || ! type N4BiasFieldCorrection &>/dev/null || ! type ImageMath &>/dev/null
        then
            echo '>> Define $ANTSPATH in your .bashrc profile. Assure that antsRegistration, antsApplyTransforms, N4BiasFieldCorrection, ImageMath and antsRegistrationSyN are available.'
            exit 1
        fi
    fi


    #set linear or non-linear
    LIN=1
    LINMSG='>> For SyN registration (ANTs), warp argument needs to be set to [1] (e.g. -wrp 1 -reg 2).\nFor FNIRT registration (FSL), warp resolution must be entered in the specified manner (e.g. -wrp 10,10,10). See -help'
    if [[ -n "$WARP_" ]]
    then
        if [[ $WARP_ =~ ^[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}$ ]] || [[ $WARP_ -eq "1" ]]
        then

            if [[ $METHOD -eq "0" ]] && [[ $WARP_ =~ ^[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}$ ]]
            then
                LIN=0
                WARP=${WARP_}
            fi

            if [[ $METHOD -eq "0" ]] && [[ ! $WARP_ =~ ^[0-9]{1,3},[0-9]{1,3},[0-9]{1,3}$ ]]
            then
                echo -e $LINMSG
                exit 1
            fi

            if [[ $METHOD -eq "1" ]] && [[ $WARP_ =~ ^[1]$ ]]
            then
                LIN=0
            fi

            if [[ $METHOD -eq "1" ]] && [[ ! $WARP_ =~ ^[1]$ ]]
            then
                echo -e $LINMSG
                exit 1
            fi          

        else
            echo -e $LINMSG
            exit 1
        fi
    fi


    #set flag for rotation to common orientation
    REORIENT=0
    if [[ -n "${REORIENT_}" ]]
    then
        if [[ ${REORIENT_} -eq "0" ]] || [[ ${REORIENT_} -eq "1" ]]
        then
        REORIENT=${REORIENT_}
        else
            echo '>> Input needs to be either [1] or [0] (default: 0). See -help'
            exit 1
        fi
    fi

    #set flag for normalization
    if [[ -n "${NORM_}" ]]
    then
        if [[ ${NORM_} -eq "1" ]] || [[ ${NORM_} -eq "2" ]]
        then
        NORM=${NORM_}
            if ! type 3dUnifize &>/dev/null
            then
                echo '3dUnifize was not found. Check .bashrc profile or reinstall AFNI.'
                exit 1
            fi
        else
            echo '>> Input needs to be either [1] for T1-weighted or [2] for T2-weighted volumes. See -help'
            exit 1
        fi
    fi

    #set flag for voxel scaling
    VOX=0
    if [[ -n "${VOX_}" ]]
    then
        if [[ ${VOX_} -eq "0" ]] || [[ ${VOX_} -eq "1" ]]
        then
            VOX=${VOX_}
        else
            echo '>> Input needs to be either [0] or [1] (default: 0). See -help'
            exit 1
        fi
    fi

    #set n-step registration
    if [[ -n "${lowres_nonBE_}" ]] && [[ -n "${func_nonBE_}" ]]
    then
        #2 = 3-step/LR+N
        STEP=2
    fi

    if [[ -n "${lowres_nonBE_}" ]] && [[ -z "${func_nonBE_}" ]]
    then
        echo '>> Either set the low-res volume as native volume or specify an additional native-volume.'
        exit 1
    fi

    if [[ -z "${lowres_nonBE_}" ]]
    then
        #1 = 2-step/N
        STEP=1
    fi
    if [[ -z "${lowres_nonBE_}" ]] && [[ -z "${func_nonBE_}" ]]
    then
        #0 = 1-step/HR
        STEP=0
    fi


    #set flag for brain dilation
    voxfac=0
    if [[ -n "${voxfac_}" ]]
    then
        if [[ ${voxfac_} -gt "0" ]]
        then
        voxfac=${voxfac_}
        else
            echo '>> Input needs to be a number greater than [0]. See -help'
            exit 1
        fi
    fi

	#set fractional intensity value
thrmsg=">> Input needs to be a number (e.g. -f 0.8). Entering [n] will propose 3 default thresholds during the procedure. For multi-step registration either enter a single paramater or parameters matching the registration steps (e.g. -f 0.2,0.3,0.4 for 3-step). See -help"
    if [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]] || [[ ${THR_} == "n" ]] || [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]] || [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
    then

		if [[ $STEP -eq "0" ]]
		then
		    if [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]] || [[ ${THR_} == "n" ]]
		    then
		    	THR=${THR_}
			else
				echo $thrmsg
				exit 1
			fi
		fi

		if [[ $STEP -eq "1" ]]
		then
		    if [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]] || [[ ${THR_} == "n" ]] || [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
		    then
		    	THR=${THR_}
			else
				echo $thrmsg
				exit 1
			fi
		fi

		if [[ $STEP -eq "2" ]]
		then
		    if [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]] || [[ ${THR_} == "n" ]] || [[ ${THR_} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
		    then
		    	THR=${THR_}
			else
				echo $thrmsg
				exit 1
			fi
		fi

    else
        echo $thrmsg
        exit 1
    fi

    #set flag for low-res mode
    LOWRES=0
    if [[ -n "${LOWRES_}" ]] && [[ $LIN -eq "0" ]]
    then
        if [[ ${LOWRES_} -eq "0" ]] || [[ ${LOWRES_} -eq "1" ]] || [[ ${LOWRES_} -eq "2" ]]
        then



    if [[ ${LOWRES_} -eq "1" ]]
    then
    LOWRES=1
    fi

    if [[ ${LOWRES_} -eq "2" ]]
    then
    LOWRES=2
    fi
        else
            echo '>> Input needs to be either [1] or [2] (default: 0). See -help'
            exit 1
        fi
    fi

    #prep endregion

#/********************/
#/********************/
#/********************/
#/********************/

#functions region
    declare -A output
    ic=0

    up_time() {
    start=$1
    end=$2
    process="$3"

    dt=$(echo "$end - $start" | bc)
    dd=$(echo "$dt/86400" | bc)
    dt2=$(echo "$dt-86400*$dd" | bc)
    dh=$(echo "$dt2/3600" | bc)
    dt3=$(echo "$dt2-3600*$dh" | bc)
    dm=$(echo "$dt3/60" | bc)
    ds=$(echo "$dt3-60*$dm" | bc)

    result=$(printf ": %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds)
    output+=([$ic+1]=$(echo "${process} ${result} \n"))
    }

    check_file() {
    tmp=$1
    fin=$2

    if [[ -f "${tmp}" ]]
    then
        if [[ "${tmp}" == *'.nii.gz'* ]]
            then
                #check volume validity
                if [[ `$FSLDIR/bin/imtest "${tmp}"` -ne 1 ]]
                then
                 echo "${tmp} is not a valid input volume."
                 exit 1
                fi
            cp -f ${tmp} ${tmp%%.*}_.nii.gz
            eval "${fin}"="${tmp%%.*}_.nii.gz"
            else
            echo ">> .nii.gz file extension expected."
            exit 1
         fi
    else
        echo ">>" ${tmp} "could not be found! Correct the entered filename and path."
        exit 1
    fi

    }

    report() {
    for (( c=1; c<=3; c++ ))
    do  
        echo ">>" | tee -a log.txt
    done
    echo -e ">> Summary:" | tee -a log.txt
    echo ">" $0 $ARGS | tee -a log.txt
    printf "${output[@]}" | tee -a log.txt
    }


    detvoxsize()
    {
    filename=$1
    tar=$2
    tar_=$3
            xval=$(fslval $filename pixdim1)
            yval=$(fslval $filename pixdim2)
            zval=$(fslval $filename pixdim3)

            FACx=$(printf %.0f $(echo "$tar/$xval" | bc -l))
            FACy=$(printf %.0f $(echo "$tar/$yval" | bc -l))
            FACz=$(printf %.0f $(echo "$tar/$zval" | bc -l))

            FAC=($FACx $FACy $FACz)
            maxFAC=${FAC[0]}
            for n in "${FAC[@]}"
            do
                [[ $n > $maxFAC ]] && maxFAC=$n
            done

            if [[ $(echo "$maxFAC > 1" | bc -l) ]]
            then
            #printf %.2f $(echo "$float/1.18" | bc -l)
                nxval=$( printf "%.1f\n" $(echo "scale=1; ($xval * $maxFAC)" | bc -l) )
                nyval=$( printf "%.1f\n" $(echo "scale=1; ($yval * $maxFAC)" | bc -l) )
                nzval=$( printf "%.1f\n" $(echo "scale=1; ($zval * $maxFAC)" | bc -l) )
                echo "> Upscale factor estimation: $maxFAC" | tee -a log.txt
            fi

            if [[ ! $(echo "$nxval >= 1" | bc -l) ]] || [[ ! $(echo "$nyval >= 1" | bc -l) ]] || [[ ! $(echo "$nzval >= 1" | bc -l) ]]
            then
                FACx=$(printf %.0f $(echo "$tar_/$xval" | bc -l))
                FACy=$(printf %.0f $(echo "$tar_/$yval" | bc -l))
                FACz=$(printf %.0f $(echo "$tar_/$zval" | bc -l))

                FAC=($FACx $FACy $FACz)
                maxFAC=${FAC[0]}
                for n in "${FAC[@]}"
                do
                    [[ $n > $maxFAC ]] && maxFAC=$n
                done
                if [[ $(echo "$maxFAC > 1" | bc -l) ]]
                then
                    nxval=$( printf "%.1f\n" $(echo "scale=1; ($xval * $maxFAC)" | bc -l) )
                    nyval=$( printf "%.1f\n" $(echo "scale=1; ($yval * $maxFAC)" | bc -l) )
                    nzval=$( printf "%.1f\n" $(echo "scale=1; ($zval * $maxFAC)" | bc -l) )
                    echo "> Upscale factor estimation: $maxFAC" | tee -a log.txt
                fi                   
            fi
            
            #fallback solution
            if [[ ! $(echo "$nxval >= 1" | bc -l) ]] || [[ ! $(echo "$nyval >= 1" | bc -l) ]] || [[ ! $(echo "$nzval >= 1" | bc -l) ]]
            then
            maxFAC=10
            fi

    }

    chvoxsize()
    {
    filename=$1
    factor=$2
        xval=$(fslval $filename pixdim1)
        yval=$(fslval $filename pixdim2)
        zval=$(fslval $filename pixdim3)

        nxval=$( printf "%.1f\n" $(echo "($xval * $factor)" | bc -l) )
        nyval=$( printf "%.1f\n" $(echo "($yval * $factor)" | bc -l) )
        nzval=$( printf "%.1f\n" $(echo "($zval * $factor)" | bc -l) )

        echo "> (Temp.) voxel dimension scaling $filename to $nxval $nyval $nzval using factor $factor" | tee -a log.txt
        cp -f $filename ${filename%%.*}orig_.nii.gz
        $FSLDIR/bin/fslchpixdim $filename $nxval $nyval $nzval
        $FSLDIR/bin/fslorient -setqformcode 1 $filename        
    }

    normalize()
    {
    filename=$1

        case $NORM in
        "1")
        MSG=$(echo -e "> Intensity normalization: $filename \n")
        echo -e "$MSG" | tee -a log.txt
        output+=([$ic+1]=$(echo ""${MSG}" \n"))
        3dUnifize -overwrite -GM -prefix $filename -input $filename | tee -a log.txt
        ;;
        "2")
        MSG=$(echo -e "> Intensity normalization: $filename \n")
        echo -e "$MSG" | tee -a log.txt
        output+=([$ic+1]=$(echo ""${MSG}" \n"))
        3dUnifize -overwrite -GM -T2 -prefix $filename -input $filename | tee -a log.txt
        ;;
        esac
    }


    pre_extraction() {
    #provisional brain-extraction
    filename=$1
    out=$2
    frct=$3

        cp -f $filename ${filename%%.*}orig.nii.gz

        #normalization
        normalize $filename

        #check for time dimension and extract 3D for ANTs
            TAXIS=$(fslval $filename dim4)

            if [[ $METHOD -eq "1" ]] && [[ $TAXIS -gt "1" ]]
            then
                DIM=$(echo "-d 4")
                ImageMath 4 $filename ExtractSlice $filename 1
                wait
                cp $filename ${filename%%.*}temp_header.nii.gz
            else
                cp $filename ${filename%%.*}temp_header.nii.gz
            fi

        #temporarily change voxel size for prelim segmentation
        if [[ $METHOD -eq "0" ]] && [[ $LIN -eq "0" ]] && [[ $VOX -eq "1" ]]
        then            
            echo "> Skipping another upscaling step."
        else
            detvoxsize "$filename" "1.5" "2"
            chvoxsize "$filename" "$maxFAC"
        fi


        preBE_start=$(date +%s.%N)
        echo "> Provisional (BET) segmentation ($frct): $filename" | tee -a log.txt

        #BET binary mask 
            if [[ $frct == "n" ]]
            then
                $FSLDIR/bin/bet $filename ${filename%%.*}temp_option_1 -f 0.3 -R -g 0 -m | tee -a log.txt
                wait
                $FSLDIR/bin/bet $filename ${filename%%.*}temp_option_2 -f 0.5 -R -g 0 -m | tee -a log.txt
                wait
                $FSLDIR/bin/bet $filename ${filename%%.*}temp_option_3 -f 0.8 -R -g 0 -m | tee -a log.txt
                wait
                fsleyes ${filename%%.*}temp_option_1.nii.gz &
                fsleyes ${filename%%.*}temp_option_2.nii.gz &
                fsleyes ${filename%%.*}temp_option_3.nii.gz &
        	    for (( c=1; c<=3; c++ ))
        	    do  
        	    echo ">>" | tee -a log.txt
        	    done
                echo -e "> Shall we proceed with option 1 (-f 0.3), option 2 (-f 0.5) or option 3 (-f 0.8)?\n> In addition, an arbitrary fractional intensity threshold can be entered with option 4.\n> Enter a number from [1]-[4] and close fsleyes." | tee -a log.txt
                read -p "Option: " option
                    if [[ $option =~ ^[1-4]$ ]]
                    then
            			case $option in
            			"1")
            			mask=${filename%%.*}temp_option_1_mask.nii.gz
            			;;
            			"2")
            			mask=${filename%%.*}temp_option_2_mask.nii.gz
            			;;
            			"3")
            			mask=${filename%%.*}temp_option_3_mask.nii.gz
            			;;
            			"4")
		                echo -e "> Enter parameter:" | tee -a log.txt
		                read -p "Value: " option_
		                if [[ $option_ =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
		               	then
	                	$FSLDIR/bin/bet $filename ${filename%%.*}temp_1 -f $option_ -R -g 0 -m | tee -a log.txt
	                	wait
	                	mask=${filename%%.*}temp_1_mask.nii.gz
		                else
	                     	echo ">> Invalid input." | tee -a log.txt
	                     	exit 1		                
		                fi
            			;;            	
            			esac
                    	MSG="> Proceeding with option $option"
                        echo $MSG | tee -a log.txt
                        output+=([$ic+1]=$(echo "$MSG\n"))
                    else
                     	echo ">> Input needs to be a number from [1-4]." | tee -a log.txt
                     	exit 1
                    fi

            	else
                	$FSLDIR/bin/bet $filename ${filename%%.*}temp_1 -f $frct -R -g 0 -m | tee -a log.txt
                	wait
                	mask=${filename%%.*}temp_1_mask.nii.gz
        	fi

        #create filtered volume
            #3dcalc -overwrite -prefix ${out}.nii.gz -a $filename -b $mask -expr 'a*b' | tee -a log.txt
            ${FSLDIR}/bin/fslmaths $filename -nan -mul $mask ${out}.nii.gz | tee -a log.txt
            wait

            MSG=$(printf "> Provisional BET : ${filename%%.*}")
            preBE_end=$(date +%s.%N)
            up_time $preBE_start $preBE_end "${MSG}"

        #biasfieldcorr
            if [[ $METHOD -eq "1" ]] && [[ $BIAS -eq "1" ]] 
            then
                N4BiasFieldCorrection -i ${out}.nii.gz -o ${out}.nii.gz -x $mask | tee -a log.txt
                MSG=$(echo -e "> N4BiasFieldCorrection (ANTs) : ${out}.nii.gz\n")
                echo -e "$MSG" | tee -a log.txt
                N4BiasFieldCorrection -i $filename -o $filename -x $mask | tee -a log.txt
                MSG_=$(echo -e "> N4BiasFieldCorrection (ANTs) : $filename\n")
                echo -e "$MSG_" | tee -a log.txt
                output+=([$ic+1]=$(echo ""${MSG}" \n"))
                output+=([$ic+1]=$(echo ""${MSG_}" \n"))
            fi

        #restore original header
        ${FSLDIR}/bin/fslcpgeom ${filename%%.*}temp_header.nii.gz ${out}.nii.gz
        ${FSLDIR}/bin/fslcpgeom ${filename%%.*}temp_header.nii.gz $filename
        $FSLDIR/bin/fslorient -setqformcode 0 ${out}.nii.gz
        $FSLDIR/bin/fslorient -setqformcode 0 $filename
    }

    binary_mask() {
    filename=$1
    ftype=$2
        #rethreshold binary mask to prevent weighted average 
        ${FSLDIR}/bin/fslmaths ${standard_BE%%.*}${ftype}_msk.nii.gz -thr 0.001 -bin ${standard_BE%%.*}${ftype}_msk_.nii.gz | tee -a log.txt
        wait
        #3dcalc -overwrite -prefix ${filename%%.*}brain.nii.gz -a ${filename%%.*}orig.nii.gz -b ${standard_BE%%.*}${ftype}_msk.nii.gz -expr 'a*b'
        ${FSLDIR}/bin/fslmaths ${filename%%.*}orig.nii.gz -nan -mul ${standard_BE%%.*}${ftype}_msk.nii.gz ${filename%%.*}brain_.nii.gz | tee -a log.txt
        cp -f ${filename%%.*}brain_.nii.gz ${filename%%.*}brain.nii.gz
        rm *'msk'*

    if [[ $METHOD -eq "0" ]] && [[ $LIN -eq "0" ]] && [[ $VOX -eq "1" ]]
    then
        ${FSLDIR}/bin/fslcpgeom ${filename%%.*}orig_.nii.gz ${filename%%.*}brain.nii.gz
    fi
    
    }

    applytransform() {
    BE=$1
    nonBE=$2
    ftype=$3
    MTXPASS=$4

    case $METHOD in
       "0")
       #FSL
        if [[ $LIN -eq "1" ]]
            then
                ${FSLDIR}/bin/flirt -in ${standard_BE%%.*}std_mask.nii.gz -ref ${BE} -applyxfm -init std2${ftype}.mat -out ${standard_BE%%.*}${ftype}_msk.nii.gz | tee -a log.txt
            else
                ${FSLDIR}/bin/applywarp --ref=${nonBE} --in=${standard_BE%%.*}std_mask.nii.gz --warp=std2high_warp_${highres_BE%%.*} --postmat=high2${ftype}.mat --out=${standard_BE%%.*}${ftype}_msk.nii.gz | tee -a log.txt
        fi
        ;;
       "1")
      #ANTs
       if [[ $LIN -eq "1" ]]
           then
            antsApplyTransforms -d 3 -i ${standard_BE%%.*}std_mask.nii.gz -r ${BE} -o ${standard_BE%%.*}${ftype}_msk.nii.gz $MTXPASS | tee -a log.txt
            else
            antsApplyTransforms -d 3 -i ${standard_BE%%.*}std_mask.nii.gz -r ${BE} -o ${standard_BE%%.*}${ftype}_msk.nii.gz $MTXPASS -t std2high_warp_${highres_BE%%.*}.nii.gz -t std2high_warp_${highres_BE%%.*}.mat | tee -a log.txt
       fi
        ;;
    esac

    }

    showmet()
    {
        if [[ $METHOD -eq "0" ]]
        then
            if [[ $LIN -eq "1" ]]
            then
            local MET="FLIRT"
            else
            local MET="FNIRT"
            fi
        fi

        if [[ $METHOD -eq "1" ]]
        then
            if [[ $LIN -eq "1" ]]
            then
            local MET="ANTs"
            else
            local MET="SyN"
            fi
        fi
    echo "$MET"
    }


    #functions endregion

#/********************/
#/********************/
#/********************/
#/********************/

#check existence and set variables
    check_file $standard_BE_ 'standard_BE'
    check_file $standard_nonBE_ 'standard_nonBE'

    check_file $highres_nonBE_ 'highres_nonBE'

    if [[ -n "$lowres_nonBE_" ]]
    then
        check_file $lowres_nonBE_ 'lowres_nonBE'
    fi
    if [[ -n "$func_nonBE_" ]]
    then
        check_file $func_nonBE_ 'func_nonBE'
    fi

#start log
echo -e "\n============" | tee -a log.txt
echo "> atlasBREX [1.5]" | tee -a log.txt
echo -e "============\n" | tee -a log.txt
    echo ">> $(date)" | tee -a log.txt
    echo ">> PID: $$" | tee -a log.txt
    echo ">> Processing:" | tee -a log.txt
    output+=([$ic+1]=$(echo "> $(date) \n"))

#timepoint start
    total_start=$(date +%s.%N)

#/********************/
#/********************/

#reorient to MNI152
    if [[ $REORIENT -eq "0" ]]
    then
        ${FSLDIR}/bin/fslreorient2std $standard_BE $standard_BE | tee -a log.txt
        ${FSLDIR}/bin/fslreorient2std $standard_nonBE $standard_nonBE | tee -a log.txt
        MSG=$(echo -e "> (Temp.) rotating template to match MNI152 orientation \n")
        echo -e "$MSG" | tee -a log.txt
        output+=([$ic+1]=$(echo ""${MSG}" \n"))
    fi

    if [[ $REORIENT -eq "0" ]]
    then
        ${FSLDIR}/bin/fslreorient2std $highres_nonBE $highres_nonBE | tee -a log.txt

        if [[ -n "$lowres_nonBE" ]] ; then
        ${FSLDIR}/bin/fslreorient2std $lowres_nonBE $lowres_nonBE | tee -a log.txt
        fi

        if [[ -n "$func_nonBE" ]] ; then
        ${FSLDIR}/bin/fslreorient2std $func_nonBE $func_nonBE | tee -a log.txt
        fi   

        MSG=$(echo -e "> (Temp.) rotating target volumes to match MNI152 orientation \n")
        echo -e "$MSG" | tee -a log.txt
        output+=([$ic+1]=$(echo ""${MSG}" \n"))
    fi

#/********************/
#/********************/


#change voxel size for FNIRT
    if [[ $METHOD -eq "0" ]] && [[ $LIN -eq "0" ]] && [[ $VOX -eq "1" ]]
    then
        detvoxsize "$highres_nonBE" "1.5" "2"
        chvoxsize "$standard_BE" "$maxFAC"
        chvoxsize "$standard_nonBE" "$maxFAC"
    fi

#create_atlas_mask
    msk_opt=$(echo $MASK | cut -d"," -f1)
    mask_start=$(date +%s.%N)
        case $msk_opt in
            "a")
            ERO_=$(echo $MASK | cut -d"," -f2)
            DIL_=$(echo $MASK | cut -d"," -f3)
            if [[ $ERO_ -gt "0" ]] ; then ERO=$(echo "-erode $ERO_" ) ; fi
            if [[ $DIL_ -gt "0" ]] ; then DIL=$(echo "-dilate $DIL_" ) ; fi
            3dAutomask $DIL $ERO -overwrite -prefix ${standard_BE%%.*}std_mask.nii.gz $standard_BE | tee -a log.txt
            MSG="> Atlas mask created using 3dAutomask ($MASK): ${standard_BE%%.*}std_mask.nii.gz"
            echo $MSG | tee -a log.txt
            output+=([$ic+1]=$(echo $MSG '\n'))
            ;;
            "b")
            BTHR_=$(echo $MASK | cut -d"," -f2)
            ERO_=$(echo $MASK | cut -d"," -f3)
            DIL_=$(echo $MASK | cut -d"," -f4)
            if [[ $BTHR_ > "0" ]] ; then BTHR=$(echo "-thrp $BTHR_" ) ; fi
            if [[ $ERO_ -gt "0" ]]
            then
                for (( c=1; c<=$ERO_; c++ ))
                do  
                    ERO+="-ero "
                done    
            fi
            if [[ $DIL_ -gt "0" ]]
            then
                for (( c=1; c<=$DIL_; c++ ))
                do  
                    DIL+="-dilD "
                done    
            fi
            ${FSLDIR}/bin/fslmaths $standard_BE $BTHR $DIL $ERO -bin ${standard_BE%%.*}std_mask.nii.gz | tee -a log.txt
            MSG="> Atlas mask created using fslmaths ($MASK): ${standard_BE%%.*}std_mask.nii.gz"
            echo $MSG | tee -a log.txt
            output+=([$ic+1]=$(echo $MSG '\n'))
            ;;
        esac   
        mask_end=$(date +%s.%N)
        up_time $mask_start $mask_end "> Atlas binary mask"

#normalization
    normalize $standard_BE
    normalize $standard_nonBE

#change voxel size for FNIRT
   if [[ $METHOD -eq "0" ]] && [[ $LIN -eq "0" ]] && [[ $VOX -eq "1" ]]
    then
        chvoxsize "$highres_nonBE" "$maxFAC"

        if [[ -n "$lowres_nonBE" ]] ; then
        chvoxsize "$lowres_nonBE" "$maxFAC"
        fi

        if [[ -n "$func_nonBE" ]] ; then
        chvoxsize "$func_nonBE" "$maxFAC"
        fi        
    fi

#provisional brain-extraction
    if [[ ${THR} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
    then
    	f1=$(echo $THR | cut -d"," -f1)
    	f2=$(echo $THR | cut -d"," -f2)
    	f3=$(echo $THR | cut -d"," -f3)
	fi

    if [[ ${THR} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*),([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
    then
    	f1=$(echo $THR | cut -d"," -f1)
    	f2=$(echo $THR | cut -d"," -f2)
	fi

    if [[ ${THR} == "n" ]] || [[ ${THR} =~ ^([0-9]*[1-9][0-9]*(\.[0-9]+)?|[0]*\.[0-9]*[1-9][0-9]*)$ ]]
    then
    	f1=$THR
	fi

    if [[ ! -f ${highres_nonBE%%.*}tmpbrain.nii.gz && -e $highres_nonBE ]] ; then
        pre_extraction $highres_nonBE ${highres_nonBE%%.*}tmpbrain "$f1"
        wait
        highres_BE=${highres_nonBE%%.*}tmpbrain.nii.gz
    fi

    if [[ ! -f ${lowres_nonBE%%.*}tmpbrain.nii.gz && -e $lowres_nonBE && $STEP -eq "2" ]] ; then
		if [[ -n "$f2" ]]
		then
			f1=$f2
		fi
        pre_extraction $lowres_nonBE ${lowres_nonBE%%.*}tmpbrain "$f1"
        wait
        lowres_BE=${lowres_nonBE%%.*}tmpbrain.nii.gz
    fi

    if [[ ! -f ${func_nonBE%%.*}tmpbrain.nii.gz && -e $func_nonBE && $STEP -gt "0" ]] ; then
 		
        if [[ $STEP == "2" ]] ; then
            if [[ -n "$f3" ]]
            then
                f1=$f3
            fi
        fi

        if [[ $STEP == "1" ]] ; then
            if [[ -n "$f2" ]]
            then
                f1=$f2
            fi
        fi

        pre_extraction $func_nonBE ${func_nonBE%%.*}tmpbrain "$f1"
        wait
        func_BE=${func_nonBE%%.*}tmpbrain.nii.gz
    fi

#/********************/
#/********************/

#highres_linear
    highres_start=$(date +%s.%N)
    case $METHOD in
       "0")
       #FSL
            echo '> FLIRT linear 1-step registration: standard -> highres' | tee -a log.txt
            ${FSLDIR}/bin/flirt -ref $highres_BE -in $standard_BE -omat std2high.mat | tee -a log.txt
        ;;
       "1")
       #ANTs
            echo '> ANTs linear registration of standard -> highres' | tee -a log.txt
            bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -t a -f $highres_BE -m $standard_BE -o std2high -j 0 | tee -a log.txt
            mv -f std2high0GenericAffine.mat std2high.mat
            find . -maxdepth 1 -name "*Warped*" -delete
        ;;
    esac

    echo '> Transformation and mask application: highres volume' | tee -a log.txt
    case $METHOD in
       "0")
       #FSL
            ${FSLDIR}/bin/flirt -in ${standard_BE%%.*}std_mask.nii.gz -ref $highres_BE -applyxfm -init std2high.mat -out ${standard_BE%%.*}high_msk.nii.gz | tee -a log.txt
        ;;
       "1")
       #ANTs
            antsApplyTransforms -d 3 -i ${standard_BE%%.*}std_mask.nii.gz -r $highres_BE -o ${standard_BE%%.*}high_msk.nii.gz -t std2high.mat | tee -a log.txt
        ;;
    esac
    wait
    binary_mask $highres_nonBE high
    wait

    highres_BE=${highres_nonBE%%.*}brain_.nii.gz

    highres_lin=$(echo -e "> $(date) / Output : ${highres_nonBE%%.*}brain.nii.gz")
    echo $highres_lin | tee -a log.txt
    output+=([$ic+1]=$(echo $highres_lin '\n'))

#create dilation
    if [[ $voxfac -gt "0" ]]
    then

    for (( c=1; c<=$voxfac; c++ ))
    do  
        diln+="-dilD "
    done

    echo "> Creating dilated ($voxfac) brain templates" | tee -a log.txt
    ${FSLDIR}/bin/fslmaths $highres_BE $BTHR $diln -bin ${highres_nonBE%%.*}dil_tmp_msk.nii.gz | tee -a log.txt
    wait
    ${FSLDIR}/bin/fslmaths $highres_nonBE -nan -mul ${highres_nonBE%%.*}dil_tmp_msk.nii.gz ${highres_nonBE%%.*}brain_tmp.nii.gz | tee -a log.txt
    wait
    ${FSLDIR}/bin/fslcpgeom $highres_nonBE ${highres_nonBE%%.*}brain_tmp.nii.gz
    wait
    ohighres_nonBE=$highres_nonBE
    highres_nonBE=${highres_nonBE%%.*}brain_tmp.nii.gz


    cp $standard_BE ${standard_BE%%.*}tmp_dil.nii.gz
    ${FSLDIR}/bin/fslmaths ${standard_BE%%.*}tmp_dil.nii.gz $BTHR $diln -bin ${standard_BE%%.*}dil_tmp_msk.nii.gz | tee -a log.txt
    wait
    ${FSLDIR}/bin/fslmaths $standard_nonBE -nan -mul ${standard_BE%%.*}dil_tmp_msk.nii.gz ${standard_BE%%.*}brain_tmp.nii.gz | tee -a log.txt
    wait
    ${FSLDIR}/bin/fslcpgeom $standard_nonBE ${standard_BE%%.*}brain_tmp.nii.gz
    ostandardBE_nonBE=$standard_nonBE
    standard_nonBE=${standard_BE%%.*}brain_tmp.nii.gz  
    fi


#/********************/
#/********************/

#highres_non_linear
    if [[ $LIN -eq "0" ]]
    then
        if [[ ! -f std2high_warp_${highres_BE%%.*}.nii.gz ]]
        then

            case $METHOD in
               "0")
               #FSL
                    #create dilated highres_mask
                    ${FSLDIR}/bin/fslmaths $highres_BE $BTHR -dilD -bin ${highres_BE%%.*}_temp_mask.nii.gz | tee -a log.txt
                    ${FSLDIR}/bin/fslcpgeom $highres_nonBE ${highres_BE%%.*}_temp_mask.nii.gz
                    wait

                    if [[ $LOWRES -eq "0" ]]
                    then
                    echo '> FNIRT non-linear 1-step registration: standard -> highres with --warpres='${WARP} 'and --regmod='${REGM} | tee -a log.txt
                    ${FSLDIR}/bin/fnirt --in=$standard_nonBE --aff=std2high.mat --cout=std2high_warp_${highres_BE%%.*} \
                    --ref=$highres_nonBE --warpres=${WARP} --regmod=$REGM --intmod=global_non_linear_with_bias \
                    --intorder=5 --biasres=50,50,50 --refmask=${highres_BE%%.*}_temp_mask.nii.gz --miter=5,5,5,5,5,10 \
                    --subsamp=4,4,2,2,1,1 --applyinmask=0 --applyrefmask=0,0,0,0,1,1 --lambda=300,150,100,50,40,30 \
                    --infwhm=8,6,5,4,2,0 --reffwhm=8,6,5,4,2,0 --estint=1,1,1,1,1,0 --numprec=float --verbose --splineorder=3 | tee -a log.txt
                    fi
                    if [[ $LOWRES -eq "1" ]]
                    then
                    echo '> FNIRT non-linear 1-step registration: skullstripped standard -> highres with --warpres='${WARP} 'and --regmod='${REGM} | tee -a log.txt
                    ${FSLDIR}/bin/fnirt --in=$standard_BE --aff=std2high.mat --cout=std2high_warp_${highres_BE%%.*} \
                    --ref=$highres_nonBE --warpres=${WARP} --regmod=$REGM --intmod=global_non_linear_with_bias \
                    --intorder=5 --biasres=50,50,50 --refmask=${highres_BE%%.*}_temp_mask.nii.gz --miter=5,5,5,5,5,10 \
                    --subsamp=4,4,2,2,1,1 --applyinmask=0 --applyrefmask=0,0,0,0,1,1 --lambda=300,150,100,50,40,30 \
                    --infwhm=8,6,5,4,2,0 --reffwhm=8,6,5,4,2,0 --estint=1,1,1,1,1,0 --numprec=float --verbose --splineorder=3 | tee -a log.txt
                    fi
                    if [[ $LOWRES -eq "2" ]]
                    then
                    echo '> FNIRT non-linear 1-step registration: skullstripped standard -> skullstripped highres with --warpres='${WARP} 'and --regmod='${REGM} | tee -a log.txt
                    ${FSLDIR}/bin/fnirt --in=$standard_BE --aff=std2high.mat --cout=std2high_warp_${highres_BE%%.*} \
                    --ref=$highres_BE --warpres=${WARP} --regmod=$REGM --intmod=global_non_linear_with_bias \
                    --intorder=5 --biasres=50,50,50 --refmask=${highres_BE%%.*}_temp_mask.nii.gz --miter=5,5,5,5,5,10 \
                    --subsamp=4,4,2,2,1,1 --applyinmask=0 --applyrefmask=0,0,0,0,1,1 --lambda=300,150,100,50,40,30 \
                    --infwhm=8,6,5,4,2,0 --reffwhm=8,6,5,4,2,0 --estint=1,1,1,1,1,0 --numprec=float --verbose --splineorder=3 | tee -a log.txt
                    fi               
                ;;
               "1")
               #ANTs
                    if [[ $LOWRES -eq "0" ]]
                    then
                    echo '> SyN non-linear 1-step registration of standard -> highres' | tee -a log.txt
                    bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -f $highres_nonBE -m $standard_nonBE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
                    mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
                    mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
                    find . -maxdepth 1 -name "*InverseWarp*" -delete
                    find . -maxdepth 1 -name "*Warped*" -delete
                    fi
                    if [[ $LOWRES -eq "1" ]]
                    then
                    ${FSLDIR}/bin/fslmaths $highres_BE $BTHR -dilD -bin ${highres_BE%%.*}_temp_mask.nii.gz | tee -a log.txt
                    ${FSLDIR}/bin/fslcpgeom $highres_nonBE ${highres_BE%%.*}_temp_mask.nii.gz
                    echo '> SyN non-linear 1-step registration of standard ->  highres with mask' | tee -a log.txt
                    bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -x ${highres_BE%%.*}_temp_mask.nii.gz -f $highres_nonBE -m $standard_nonBE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
                    mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
                    mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
                    find . -maxdepth 1 -name "*InverseWarp*" -delete
                    find . -maxdepth 1 -name "*Warped*" -delete
                    fi
                    if [[ $LOWRES -eq "2" ]]
                    then
                    echo '> SyN non-linear 1-step registration of skullstripped standard -> skullstripped highres' | tee -a log.txt
                    bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -f $highres_BE -m $standard_BE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
                    mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
                    mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
                    find . -maxdepth 1 -name "*InverseWarp*" -delete
                    find . -maxdepth 1 -name "*Warped*" -delete
                    fi                     
                ;;
            esac
        else
        echo '> Using pre-existent' std2high_warp_${highres_BE%%.*}.nii.gz | tee -a log.txt
        if [[ $METHOD -eq "1" ]] && [[ ! -f std2high_warp_${highres_BE%%.*}.mat ]]
        then
            echo ">> std2high_warp_${highres_BE%%.*}.mat was not found. Renaming std2high_warp_${highres_BE%%.*}.nii.gz and performing non-linear registration" | tee -a log.txt
            mv -f std2high_warp_${highres_BE%%.*}.nii.gz std2high_warp_${highres_BE%%.*}_bak.nii.gz

            if [[ $LOWRES -eq "0" ]]
            then
            echo "> SyN non-linear 1-step registration of standard -> highres" | tee -a log.txt
            bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -f $highres_nonBE -m $standard_nonBE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
            mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
            mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
            find . -maxdepth 1 -name "*InverseWarp*" -delete
            find . -maxdepth 1 -name "*Warped*" -delete
            fi
            if [[ $LOWRES -eq "1" ]]
            then
            ${FSLDIR}/bin/fslmaths $highres_BE $BTHR -dilD -bin ${highres_BE%%.*}_temp_mask.nii.gz | tee -a log.txt
            ${FSLDIR}/bin/fslcpgeom $highres_nonBE ${highres_BE%%.*}_temp_mask.nii.gz
            echo "> SyN non-linear 1-step registration of standard -> highres with mask" | tee -a log.txt
            bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -x ${highres_BE%%.*}_temp_mask.nii.gz -f $highres_nonBE -m $standard_nonBE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
            mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
            mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
            find . -maxdepth 1 -name "*InverseWarp*" -delete
            find . -maxdepth 1 -name "*Warped*" -delete
            fi            
            if [[ $LOWRES -eq "2" ]]
            then
             echo '> SyN non-linear 1-step registration of skullstripped standard -> skullstripped highres' | tee -a log.txt
            bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -p f -t b -f $highres_BE -m $standard_BE -i std2high.mat -j 0 -o std2high_ | tee -a log.txt
            mv -f std2high_1Warp.nii.gz std2high_warp_${highres_BE%%.*}.nii.gz
            mv -f std2high_0GenericAffine.mat std2high_warp_${highres_BE%%.*}.mat
            find . -maxdepth 1 -name "*InverseWarp*" -delete
            find . -maxdepth 1 -name "*Warped*" -delete
            fi  
        fi
        fi

    echo '> Transformation and mask application: highres volume' | tee -a log.txt
    case $METHOD in
       "0")
       #FSL
            ${FSLDIR}/bin/applywarp --ref=$highres_nonBE --in=${standard_BE%%.*}std_mask.nii.gz --warp=std2high_warp_${highres_BE%%.*} --out=${standard_BE%%.*}high_msk.nii.gz | tee -a log.txt
        ;;
       "1")
       #ANTs
            antsApplyTransforms -d 3 -i ${standard_BE%%.*}std_mask.nii.gz -r $highres_nonBE -o ${standard_BE%%.*}high_msk.nii.gz -t std2high_warp_${highres_BE%%.*}.nii.gz -t std2high_warp_${highres_BE%%.*}.mat | tee -a log.txt
        ;;
    esac

        if [[ $voxfac -gt "0" ]]
        then
            highres_nonBE=$ohighres_nonBE
            standard_nonBE=$ostandard_nonBE
        fi

        mv -f ${highres_nonBE%%.*}brain.nii.gz ${highres_nonBE%%.*}brain_lin.nii.gz
        rename=$(echo 'Appended _lin to' ${highres_nonBE%%.*}brain.nii.gz)
        echo $rename | tee -a log.txt
        output+=([$ic+1]=$(echo $rename '\n'))
        wait

        rm ${highres_nonBE%%.*}brain_.nii.gz
        binary_mask $highres_nonBE high
        wait
        highres_BE=${highres_nonBE%%.*}brain_.nii.gz
        highres_nonlin=$(echo "> $(date) / $(showmet) / Output : ${highres_nonBE%%.*}brain.nii.gz")
        echo $highres_nonlin | tee -a log.txt
        output+=([$ic+1]=$(echo $highres_nonlin '\n'))
    fi

    highres_end=$(date +%s.%N)
    up_time $highres_start $highres_end '> atlasBREX runtime: highres'

#/********************/
#/********************/

#highres-only
    if [[ $STEP -eq "0" ]]
    then
        #timepoint end
        total_end=$(date +%s.%N)
        up_time $total_start $total_end '> Total runtime'
        output+=([$ic+1]=$(echo "> $(date) \n"))
        report
        exit
    fi

#/********************/
#/********************/

#highres -> lowres -> functional
    native_start=$(date +%s.%N)

    if [[ $STEP -eq "2" ]]
    then
        case $METHOD in
           "0")
           #FSL
                echo '> FLIRT linear 2-step registration: highres -> lowres -> functional'
                ${FSLDIR}/bin/flirt -dof 6 -in $lowres_BE -ref $func_BE -omat low2func.mat | tee -a log.txt
                lowres_start=$(date +%s.%N)   
                ${FSLDIR}/bin/flirt -dof 12 -in $highres_BE -ref $lowres_BE -omat high2low.mat | tee -a log.txt
                wait
                ${FSLDIR}/bin/convert_xfm -omat high2func.mat -concat high2low.mat low2func.mat | tee -a log.txt
                wait
                if [[ ! $LIN -eq "0" ]]
                then
                    ${FSLDIR}/bin/convert_xfm -omat std2low.mat -concat std2high.mat high2low.mat | tee -a log.txt
                    wait
                    ${FSLDIR}/bin/convert_xfm -omat std2func.mat -concat std2high.mat high2func.mat | tee -a log.txt        
                fi
            ;;
           "1")
           #ANTs
                bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -t a -f $func_BE -m $lowres_BE -o low2func | tee -a log.txt
                mv -f low2func0GenericAffine.mat low2func.mat
                find . -maxdepth 1 -name "*Warped*" -delete
                lowres_start=$(date +%s.%N)  
                bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -t a -f $lowres_BE -m $highres_BE -o high2low | tee -a log.txt
                mv -f high2low0GenericAffine.mat high2low.mat
                find . -maxdepth 1 -name "*Warped*" -delete
                if [[ $LIN -eq "1" ]]
                then
                	MTXPASS=$(echo "-t high2low.mat -t std2high.mat")
            	else
            		MTXPASS=$(echo "-t high2low.mat")
            	fi
            ;;
        esac

        #/************/
        echo '> Transformation and mask application: lowres volume' | tee -a log.txt
        applytransform $lowres_BE $lowres_nonBE low "$MTXPASS"
        wait
        binary_mask $lowres_nonBE low
        lowres_fin=$(echo "> $(date) / $(showmet) / Output : ${lowres_nonBE%%.*}brain.nii.gz")
        echo $lowres_fin | tee -a log.txt
        output+=([$ic+1]=$(echo $lowres_fin '\n')) 

        lowres_end=$(date +%s.%N)
        up_time $lowres_start $lowres_end '> atlasBREX runtime: lowres'
    fi

#/********************/
#/********************/

#highres2func
    if [[ $STEP -eq "1" ]]
    then
    case $METHOD in
       "0")
       #FSL
            echo '> FLIRT linear 1-step registration: highres -> functional'
            ${FSLDIR}/bin/flirt -dof 12 -in $highres_BE -ref $func_BE -omat high2func.mat | tee -a log.txt
            if [[ ! $LIN -eq "0" ]]
            then
            ${FSLDIR}/bin/convert_xfm -omat std2func.mat -concat std2high.mat high2func.mat | tee -a log.txt
            fi
        ;;
       "1")
       #ANTs
            bash antsRegistrationSyN.sh -d 3 -n $ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS -t a -f $func_BE -m $highres_BE -o high2func | tee -a log.txt
            mv -f high2func0GenericAffine.mat high2func.mat
            find . -maxdepth 1 -name "*Warped*" -delete
            if [[ $LIN -eq "1" ]]
            then
                MTXPASS=$(echo "-t high2func.mat -t std2high.mat")
            else
            	MTXPASS=$(echo "-t high2func.mat")
            fi
        ;;
    esac
    else
        if [[ $LIN -eq "1" ]]
        then
            MTXPASS=$(echo "-t low2func.mat -t high2low.mat -t std2high.mat")
        else
        	MTXPASS=$(echo "-t low2func.mat -t high2low.mat")
        fi
    fi

#/********************/
#/********************/

#native
    echo '> Transformation and mask application: native volume' | tee -a log.txt
    applytransform $func_BE $func_nonBE func "$MTXPASS"
    wait
    binary_mask $func_nonBE func

    epi_fin=$(echo "> $(date) / $(showmet) / Output : ${func_nonBE%%.*}brain.nii.gz")
    echo $epi_fin | tee -a log.txt
    output+=([$ic+1]=$(echo $epi_fin '\n')) 

    native_end=$(date +%s.%N)
    up_time $native_start $native_end '> atlasBREX runtime: native volume'

#timepoint end
    total_end=$(date +%s.%N)
    up_time $total_start $total_end '> Total runtime'
    output+=([$ic+1]=$(echo "> $(date) \n"))

report
exit
#/********************/
#/********************/
