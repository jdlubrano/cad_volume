require 'byebug'
require 'unitwise'

require_relative 'local_asset'

class PartAnalysis
  attr_reader :x, :y, :z, :diameter, :height

  def initialize(part)
    @part = part
  end

  def run
    script = File.join(__dir__, '..', '..', 'volume.py')
    cmd = "python #{script} -f #{LocalAsset.path(@part)} | tail -n1"
    puts "Running #{cmd}"
    @result = JSON.parse(`#{cmd}`)

    if @result['error']
      puts @result.inspect
      return
    end

    if @result['cylinder_volume'] < @result['bounding_box_volume']
      cylinder = @result['bounding_cylinder']
      @diameter = inches(cylinder['radius'] * 2)
      @height = inches(cylinder['height'])
    else
      box = @result['bounding_box']
      @x = inches(box['x_length'])
      @y = inches(box['y_length'])
      @z = inches(box['z_length'])
    end
  end

  def cylindrical?
    return @x.nil?
  end

  private

  def mm(size)
    Unitwise(size, 'mm')
  end

  def inches(size)
    mm(size).convert_to('in').to_f
  end
end

