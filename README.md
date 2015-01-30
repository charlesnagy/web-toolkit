Web Toolkit
=========

Web specific tools for make my work easier (automation, optimization, capacity test etc.)

## Tools

###  Captest ###

Capacity test for websites based on url source.

Currently only support file input but I plan to add REST API calls and normal URL fetch to be able to extract that information real-time from your application. 

#### Example usage:

	python wt-capacity-test.py -s top_urls.csv -c 2 -t 10 -B http://example.com -v 4

#### Parameters:

	|		Parameter			|							Description								| Default |
	-----------------------------------------------------------------------------------------------------------
	| -s 	| --source      	| CSV file to read the urls and weights from						|         |
	| -c 	| --concurrency 	| The number of threads being spawned for fetching urls parallel.	|   60    |
	| -B 	| --base-url    	| Base url if the urls in the csv file are relative.				|   ''    |
	| -v 	| --verbosity   	| Verbosity from 0 to 4 where 0 is only Critical and 4 is Debug.	|    3    |

Help text available

	python wt-capacity-test.py --help


You can find me on [Twitter](https://twitter.com/charlesnagy "Charlesnagy Twitter"), [My Blog](http://charlesnagy.info/ "Charlesnagy.info") or [LinkedIn]("http://www.linkedin.com/in/nkaroly" "Károly Nagy - MySQL DBA")

