# Website Interpreter, Static aka wisPy (not a backronym guys I swear)
# Hayden Buscher, 2023 - Version 1.1.0

import markdown
import configparser
import os

config = configparser.ConfigParser()
md = markdown.Markdown(extensions = ['meta'])
version = '1.1.0'

# Main method
def main() -> None:

	# Get parameters
	params = configParse('wispy_config.ini')
	globalParams = params[1]
	params = params[0]

	# Create sitemap
	useMap = False
	mapPath = globalParams['root']+'sitemap.xml'
	sitemap = open(mapPath,'w')

	# Sitemap header
	sitemap.write('<!-- Generated by wisPy -->\n')
	sitemap.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

	# Parse individual folders
	for tag in range(len(params)):
		pathIn = params[tag]['input']	# Input folder path
		pathOut = params[tag]['output']	# Output folder path

		# Fill empty params with global
		for key in params[tag]:
			if params[tag][key] is None:
				params[tag][key] = globalParams[key]
		
		# Parse individual files
		for file in os.listdir(pathIn):

			# File extension parsing
			if file.lower().endswith('.md'):
				fileIn = open(pathIn+file,'r').read()	# File read from
				fileOut = open(pathOut+ os.path.splitext(file)[0] + '.html' ,'w')	# File to write to

				# Replace params with metadata
				metaTemp = metaParse(fileIn,params[tag].copy())
				fileIn = metaTemp[0]
				paramsTemp = metaTemp[1]

				if not ((not paramsTemp['draft'] is None) and paramsTemp['draft'].lower() == 'true'):
					
					# md to html conversion
					print(pathIn+file+' -> '+pathOut)
					markConvert(fileIn,fileOut,paramsTemp)
					
					# Append to sitemap
					if not paramsTemp['sitemap'] is None and paramsTemp['sitemap'].lower() == 'true':
						useMap = True
						mapAdd(pathOut+ os.path.splitext(file)[0] + '.html',sitemap,paramsTemp)
				else:
					os.remove(pathOut+ os.path.splitext(file)[0] + '.html')
	sitemap.write('</urlset>')
	# Delete sitemap if not enabled
	if not useMap:
		os.remove(mapPath)


# Add to sitemap
def mapAdd(pathIn, sitemap, params) -> None:
	sitemapParams = ['changefreq','priority','lastmod']
	sitemap.write('<url>\n')

	# Undefined url exception
	if params['url'] is None:
			exception('No url defined')

	# url
	relative = os.path.relpath(pathIn, params['root'])
	sitemap.write('<loc>'+params['url']+'/'+relative+'</loc>\n')

	# Other params
	for param in sitemapParams:
		if not params[param] is None:
			sitemap.write('<'+param+'>'+params[param]+'</'+param+'>\n')

	sitemap.write('</url>\n')


# Parse config file
def configParse(path) -> tuple:
		config.read(path)
		tags = config.sections()	# Generate list of tags
		params: list = []
		globalParams: dict = {}
		
		# Parse config sections 
		for tag in tags:	# Parse individual tags
			keys = list(config[tag].keys())	# Generate list of keys

			tempParams = {	# Dictionary of parameters
			'root':		None, 	'input':		None,	'output':		None,
		 	'template':	None,	'date':			None,	'sitemap':		None,	
			'lastmod':	None,	'priority':		None,	'changefreq':	None,	
			'draft':	None,	'publish':		None,	'gentag':		'true',	
			'prefix':	None,	'suffix':		None,	'url':			None,	
			'css':		None,	'title':		None,	'author': 		None,	
			'keywords':	None,	'description':	None,	'viewport':		None,
			}

			# Input exception
			if (not 'input' in keys or config[tag]['input'] == '') and not tag == 'global':
				exception('No input path for '+tag)
			
			for key in keys:	# Parse individual keys

				# Set and format parameters
				if key in tempParams and not config[tag][key] == '':
					tempParams[key] = config[tag][key]
					tempParams[key] = paramFormat(key,tempParams[key])

			# Blank path checking
			if tempParams['output'] is None:
				tempParams['output'] = tempParams['input']

			# Local parameters
			if not tag == 'global':
				params.append(tempParams)

			# Global parameters
			else:
				globalParams = tempParams
				if globalParams['root'] is None:
					globalParams['root'] = './'
		return (params,globalParams)


# Format single parameter
def paramFormat(key,param) -> str:
	pathParams = ['input','output','template','root','css']

	# Ensure paths end with /
	if key in pathParams:
		if not param.endswith('/') and not key == 'css' and not key == 'template':
			param = param+'/'

		# File path exception
		if not os.path.exists(param) and not key == 'css':
			exception('Path '+param+' does not exist')

		# Fill in home directory references
		if param.startswith('~'):
			param = os.path.expanduser('~')+param[1:]
	return param


# Create .html file, apply template
def markConvert(fileIn, fileOut, params) -> None: # -> None:
	template = params['template']

	# Checks if template is in use
	if not template is None:
		useTemplate = False
		
		# Writes template to file
		for line in open(template,'r').readlines():
			
			# Looks for HEAD tag, and inserts metadata
			if '<!--HEAD-->' in line:
				metaWrite(fileOut, params.copy())

			# Looks for INSERT tag, pastes data into template
			elif '<!--INSERT-->' in line:
				useTemplate = True
				fileOut.write(markdown.markdown(fileIn))
			else:
				fileOut.write(line)
				
		# Insert tag not found exception
		if not useTemplate:
			exception('Insert tag not found in template'+template)

	# Create new file if no template
	else:
		fileOut.write('<html><head>\n')
		metaWrite(fileOut, params.copy())
		fileOut.write('</head><body>\n')
		fileOut.write(markdown.markdown(fileIn))
		fileOut.write('\n</body></html>')


# Write metadata to file
def metaWrite(fileOut, params) -> None:
	tagsOpen = {
		'title':'<title>',
		'description':'<meta name=\"description\" content=\"',
		'keywords':'<meta name=\"keywords\" content=\"',
		'author':'<meta name=\"author\" content=\"',
		'viewport':'<meta name=\"viewport\" content=\"'
	}
	tagsClosed = {
		'title':'</title>',
		'description':'\">',
		'keywords':'\">',
		'author':'\">',
		'viewport':'\">'
	}

	# Print wisPy version tag
	if not params['gentag'].lower() == 'false':
		fileOut.write('<meta name=\"generator\" content=\"wisPy v'+version+'\">\n')

	# Set title
	if params['prefix'] is None:
		params['prefix'] = ''
	if params['suffix'] is None:
		params['suffix'] = ''
	if not params['title'] is None:
		params['title'] = params['prefix']+params['title']+params['suffix']

	# Generate head tags
	for key in params:
		if key in tagsOpen and not params[key] is None:
			fileOut.write(tagsOpen[key]+params[key]+tagsClosed[key]+'\n')

	# Parse css
	if not params['css'] is None:
		cssTemp = params['css'].split()
		for path in cssTemp:
			path  = paramFormat('css',path)
			fileOut.write('<link rel=\"stylesheet\" href=\"'+path+'\">\n')


# Parse metadata
def metaParse(fileIn, params) -> tuple:
	tempFile = md.convert(fileIn)

	for key in md.Meta:	# Parse individual keys	
		if key in params:
			params[key] = paramFormat(key,md.Meta[key][0])
	return (tempFile, params)


# Exception generator
def exception (string) -> None:
	print(string+', aborting.')
	exit()


if __name__ == "__main__":
    main()
