require 'awesome_print'
require 'json'

result = `python vol.py`.split("\n")
json = JSON.parse result.last
ap json

