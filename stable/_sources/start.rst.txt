Start the Viewer
----------------

To start LaVue

.. code-block:: console

   $ lavue

or

.. code-block:: console

   $ lavue3

for python 3 version (for older debian/ubuntu releases).

Start the Viewer in the expert mode
"""""""""""""""""""""""""""""""""""

Changing LaVue settings is available in the expert mode, i.e.

.. code-block:: console

   $ lavue -m expert

under an additional button: Configuration.

Launching options
"""""""""""""""""

To get all possible command-line parameters

.. code-block:: console

   $ lavue -h

   usage: lavue [-h] [-v] [-m MODE] [-y STYLE] [-e STYLESHEET] [-j INSTANCE]
		[-f IMAGEFILE] [-s SOURCE] [-c CONFIGURATION] [-z] [-o MBUFFER]
		[--channel CHANNEL] [-b BKGFILE] [-k MASKFILE] [-p MASKHIGHVALUE]
		[-t TRANSFORMATION] [-i SCALING] [-l LEVELS] [-q AUTOFACTOR]
		[-g GRADIENT] [-r VIEWRANGE] [-x] [-u TOOL] [-a TANGODEVICE]
		[-d DOORDEVICE] [-n ANALYSISDEVICE]

   2d detector live image viewer

   optional arguments:
     -h, --help            show this help message and exit
     -v, --version         program version
     -m MODE, --mode MODE  interface mode, i.e. user, expert
     -y STYLE, --style STYLE
			   Qt style
     -e STYLESHEET, --stylesheet STYLESHEET
			   Qt stylesheet
     -j INSTANCE, --instance INSTANCE
			   LaVue instance with separate configuration
     -ns, --no-space-instance
			   the configuration file name without a space character
			     (in the future major release it will become the default one)
     --organization ORGANIZATION
			   Organization name
     --domain DOMAIN
			   Organization domain name
     --configuration-path CONFIGPATH
			   Base configuration path
     -f IMAGEFILE, --image-file IMAGEFILE
			   image file name to show, e.g. /tmp/myfile2.nxs://entry/data/pilatus,,-1
     -s SOURCE, --source SOURCE
			   image source, i.e. hidra, http, tangoattr,
			       tangoevents, tangofile, doocsprop, tineprop,
			       epicspv, zmq, asapo, nxsfile, test
			   multiple-source names is separated by semicolon ';'
     -c CONFIGURATION, --configuration CONFIGURATION
			   configuration strings for the image source separated by comma, e.g.
			     hidra -> '-c haspilatus300k.desy.de'
			     http -> '-c haso228eiger/1.5.0'
			     tangoattr -> '-c sys/tg_test/1/double_image_ro'
			     tangoevents -> '-c sys/lamccds/1/video_last_image'
			     tangofile -> '-c p00/plt/1/LastImageTaken,p00/plt/1/LastImagePath'
			     zmq -> '-c haso228:5535,topic'
			     doocsprop -> '-c TTF2.FEL/BLFW2.CAM/BL0M1.CAM/IMAGE_EXT'
			     nxsfile -> '-c /tmp/myfile.nxs://entry/data/pilatus'
				     or '-c /tmp/myfile2.nxs://entry/data/pilatus,0,34'
			     tineprop -> '-c /HASYLAB/P00_LM00/Output/Frame'
			     asapo -> '-c pilatus,substream2'
			     epicspv -> '-c '00SIM0:cam1:,[640,480]'
			  configuration for multiple-sources is separated by semicolon ';'
     --offset OFFSET relative offset x,y[,TRANSFORMATION]
			   where x,y are position of the first pixel for a particular image source
			   while optional TRANSFORMATION can be:
			     flip-up-down, flipud, fud, flip-left-right, fliplr, flr, transpose, t,
			     rot90, r90, rot180, r180, r270, rot270, rot180+transpose, rot180t or r180t
			   offset for multiple-sources is separated by semicolon ';'
			   e.g.
			      ;200,300;,54;121,3
			      200,300;100,
			      200,300;100,200,t
			      ;200,300,r45;,52;11,3,r180t
     -w RANGEWINDOW, --range-window RANGEWINDOW
			   range window slices, i.e. x1:x2,y1:y2 , e.g. -w 10:500,20:200
			     where 'm' is '-'
     --ds-factor DSFACTOR integer down-sampling factor
     --ds-reduction DSREDUCTION
			   down-sampling reduction function, i.e. 'max', 'min', 'mean' or 'sum'
     -z, --filters apply image filters
     -o MBUFFER, --memory-buffer MBUFFER
			size of memory buffer in frames
     --channel CHANNEL
			default channel number or 'sum', 'mean', 'rgb' or RGB channels separated by comma e.g.'0,1,3'
     -b BKGFILE, --bkg-file BKGFILE
			   background file-name to load
     --bkg-scale BKGSCALE background scaling factor
     --bright-field-file BRIGHTFIELDFILE
			   bright field file-name to load
     --bright-field-scale BRIGHTFIELDSCALE
			bright field scaling factor
     -k MASKFILE, --mask-file MASKFILE
			mask file-name to load
     -p MASKHIGHVALUE, --mask-high-value MASKHIGHVALUE
			   highest pixel value to show
     -t TRANSFORMATION, --transformation TRANSFORMATION
			   image transformation, i.e.
			     flip-up-down, flip-left-right, transpose,
			     rot90, rot180, rot270, rot180+transpose
     --overflow OVERFLOWVALUE
                           above the overflow value all pixels are shown in a special color defined in the configuration
     -i SCALING, --scaling SCALING
			   intensity scaling, i.e. sqrt, linear, log
     -l LEVELS, --levels LEVELS
			   intensity display levels e.g. -l m20,20
			     where 'm' is '-'
			   the RGB channel levels can be added separated by ';' e.g.
			     -l '0,40;1,35;0,30;2,45;green'
				 where 0,40 are the main intensity dispay levels
				       1,35 are the red channel intensity dispay levels
				       0,30 are the green channel intensity dispay levels
				       2,45 are the blue channel intensity dispay levels
					  and the green channel level widgets are selected
     -q AUTOFACTOR, --factor AUTOFACTOR
			   factor of the highest pick for automatic levels in %, e.g. -q 0.5
     -g GRADIENT, --gradient GRADIENT
			   color gradient, i.e. grey, highcontrast, thermal, flame,
			     bipolar, spectrum, spectrumclip, greyclip, reversegrey, cyclic,
			     yellowy, inverted
			   the multi channel color gradients can be added separated by ';' e.g.  -g 'thermal;flame'
     -r VIEWRANGE, --range VIEWRANGE
			   viewbox range, i.e. xmin,ymin,xsize,ysize , e.g. -r 5.6,m60.7,543.2,444.11
			       where 'm' is '-'
     -x, --start           connect the image source
     -u TOOL, --tool TOOL  utility tool, i.e. intensity, roi, movemotors, meshscan, maxima,
			     linecut, projections, 1d-plot, angle/q, q+roi+proj, parameters, diffractogram
     --tool-configuration TOOLCONFIG
			     JSON dictionary with tool configuration, e.g. {"rows_to_plot":"0,1","buffer_size":512}
     -a TANGODEVICE, --tango-device TANGODEVICE
			   tango device of LavueController to communicated with clients during the run
     -d DOORDEVICE, --door DOORDEVICE
			   door device to communicated with sardana during the run
     -n ANALYSISDEVICE, --analysis-device ANALYSISDEVICE
			   tango analysis device of LambdaOnlineAnalysis to communicate with analysis clients during the run
     --log LOG logging level, i.e. debug, info, warning, error, critical
