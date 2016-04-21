class LocalAsset
  def self.path(part)
    File.join(__dir__, '..', 'models', part['file'])
  end
end

