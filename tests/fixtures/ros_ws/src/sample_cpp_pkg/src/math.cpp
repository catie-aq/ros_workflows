#include "sample_cpp_pkg/math.hpp"

#include <stdexcept>
#include <vector>

namespace sample_cpp_pkg
{

int clamp(int value, int low, int high)
{
  if (low > high) {
    throw std::invalid_argument("empty interval");
  }
  if (value < low) {
    return low;
  }
  if (value > high) {
    return high;
  }
  return value;
}

long sum_to(int n)
{
  std::vector<int> values;
  for (int i = 1; i <= n; ++i) {
    values.push_back(i);
  }
  long total = 0;
  for (const int value : values) {
    total += value;
  }
  return total;
}

}  // namespace sample_cpp_pkg
