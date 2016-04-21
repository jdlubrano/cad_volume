require 'awesome_print'
require 'byebug'

require_relative 'lib/part'
require_relative 'lib/part_analysis'
require_relative 'lib/step_downloader'

StepDownloader.new.get_step_files

BOX_HEADERS = %w(Part_ID File Asset_ID units length width thickness x y z).freeze

CYL_HEADERS = %w(Part_ID File Asset_ID units platform_diameter
                 platform_length diameter length).freeze

boxes_csv = [BOX_HEADERS]
cylinders_csv = [CYL_HEADERS]

def box_row(part, part_analysis)
  [
    part['id'],
    part['file'],
    part['asset_id'],
    part['units'],
    part['length'],
    part['width'],
    part['thickness'],
    part_analysis.x,
    part_analysis.y,
    part_analysis.z
  ]
end

def cylinder_row(part, part_analysis)
  [
    part['id'],
    part['file'],
    part['asset_id'],
    part['units'],
    part['diameter'],
    part['length'],
    part_analysis.diameter,
    part_analysis.height
  ]
end

Part.all do |part|
  next if part.length.nil?
  pa = PartAnalysis.new(part)
  pa.run
  if pa.cylindrical?
    cylinders_csv.push cylinder_row(part, pa)
  else
    boxes_csv.push box_row(part, pa)
  end
end

File.open('boxes.csv', 'w') do |file|
  boxes_csv.map! { |row| row.join(',') }
  file.write boxes_csv.join("\n")
end

File.open('cylinders.csv', 'w') do |file|
  cylinders_csv.map! { |row| row.join(',') }
  file.write cylinders_csv.join("\n")
end

