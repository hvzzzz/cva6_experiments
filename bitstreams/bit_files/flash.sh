#!/usr/bin/bash
set -e
XILINX=/opt/Xilinx
XILINX_VERSION=2024.1
BOOTGEN=${XILINX}/Vivado/${XILINX_VERSION}/bin/bootgen
NAME=$(basename $1)
OLDPWD=$PWD
if [ "$1" == "" ]; then
  echo "Usage: $0 <bitstream.bit>"
  exit
fi
cp $1 /tmp/bitstream.bit
cd /tmp
# This just parse the header to detect the part version
XILINX_VERSION_HEX=$(echo -n $XILINX_VERSION |
  xxd -p |
  sed "s/\(..\)/\1 /g")
PART=$(xxd -p -l 300 /tmp/bitstream.bit |
  tr -d "\n" |
  sed "s/\(..\)/\1 /g" |
  sed "s/.* ${XILINX_VERSION_HEX}00 62 00 .. //g" |
  sed "s/00 .*//g" |
  xxd -r -p)
echo "Detected part ${PART}"
if [ "$PART" == "xczu7ev-ffvc1156-2-e" ]; then
  ARCH=zynqmp
  cat >/tmp/bitstream.bif <<EOF
all: {
    [destination_device=pl] bitstream.bit
}
EOF
else
  ARCH=zynq
  cat >/tmp/bitstream.bif <<EOF
all: {
    bitstream.bit
}
EOF
fi
$BOOTGEN -arch $ARCH -image bitstream.bif -w -process_bitstream bin
rm bitstream.bit bitstream.bif
mv bitstream.bit.bin ${OLDPWD}/${NAME}.bin
